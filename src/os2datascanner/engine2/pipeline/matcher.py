from os import getpid

from ...utils.prometheus import prometheus_session
from ..rules.rule import Rule
from ..conversions.types import decode_dict
from .utilities import (notify_ready, pika_session, notify_stopping,
        prometheus_summary, json_event_processor, make_common_argument_parser)


def message_received_raw(body, channel, matches_q, handles_q, conversions_q):
    progress = body["progress"]
    representations = decode_dict(body["representations"])
    rule = Rule.from_json_object(progress["rule"])

    new_matches = []

    # Keep executing rules for as long as we can with the representations we
    # have
    while not isinstance(rule, bool):
        head, pve, nve = rule.split()

        target_type = head.operates_on
        type_value = target_type.value
        if type_value not in representations:
            # We don't have this representation -- bail out
            break
        representation = representations[type_value]

        matches = list(head.match(representation))
        new_matches.append({
            "rule": head.to_json_object(),
            "matches": matches if matches else None
        })
        if matches:
            rule = pve
        else:
            rule = nve

    if isinstance(rule, bool):
        # We've come to a conclusion!
        yield (matches_q, {
            "scan_spec": body["scan_spec"],
            "handle": body["handle"],
            "matched": rule,
            "matches": progress["matches"] + new_matches
        })
        # Only trigger metadata scanning if the match succeeded
        if rule:
            yield (handles_q, {
                "scan_tag": body["scan_spec"]["scan_tag"],
                "handle": body["handle"]
            })
    else:
        # We need a new representation to continue
        yield (conversions_q, {
            "scan_spec": body["scan_spec"],
            "handle": body["handle"],
            "progress": {
                "rule": rule.to_json_object(),
                "matches": progress["matches"] + new_matches
            }
        })


def main():
    parser = make_common_argument_parser()
    parser.description = ("Consume representations and generate matches"
            + " and fresh conversions.")

    inputs = parser.add_argument_group("inputs")
    inputs.add_argument(
            "--representations",
            metavar="NAME",
            help="the name of the AMQP queue from which representations"
                    + " should be read",
            default="os2ds_representations")

    outputs = parser.add_argument_group("outputs")
    outputs.add_argument(
            "--matches",
            metavar="NAME",
            help="the name of the AMQP queue to which matches should be"
                    + " written",
            default="os2ds_matches")
    outputs.add_argument(
            "--conversions",
            metavar="NAME",
            help="the name of the AMQP queue to which conversions should be"
                    + " written",
            default="os2ds_conversions")
    outputs.add_argument(
            "--handles",
            metavar="NAME",
            help="the name of the AMQP queue to which handles (for metadata"
                    + " extraction) should be written",
            default="os2ds_handles")

    args = parser.parse_args()

    with pika_session(args.handles, args.matches, args.conversions,
            args.representations, host=args.host, heartbeat=6000) as channel:

        @prometheus_summary(
                "os2datascanner_pipeline_matcher", "Representations examined")
        @json_event_processor
        def message_received(body, channel):
            if args.debug:
                print(channel, body)
            return message_received_raw(body, channel,
                    args.matches, args.handles, args.conversions)
        channel.basic_consume(args.representations, message_received)

        with prometheus_session(
                str(getpid()),
                args.prometheus_dir,
                stage_type="matcher"):
            try:
                print("Start")
                notify_ready()
                channel.start_consuming()
            finally:
                print("Stop")
                notify_stopping()
                channel.stop_consuming()


if __name__ == "__main__":
    main()
