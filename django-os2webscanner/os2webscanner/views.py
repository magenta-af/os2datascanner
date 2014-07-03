from operator import attrgetter

from django.shortcuts import render
from django.views.generic import View, ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Scanner, Domain, RegexRule, Scan, Match, UserProfile


class LoginRequiredMixin(View):
    """Include to require login."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class RestrictedListView(ListView, LoginRequiredMixin):
    """Make sure users only see data that belong to their own organization."""

    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        if user.is_superuser:
            return self.model.objects.all()
        else:
            profile = user.get_profile()
            return self.model.objects.filter(organization=profile.organization)


class MainPageView(TemplateView):
    template_name = 'index.html'


class ScannerList(RestrictedListView):
    """Displays list of scanners."""
    model = Scanner
    template_name = 'os2webscanner/scanners.html'


class DomainList(RestrictedListView):
    """Displays list of domains."""
    model = Domain
    template_name = 'os2webscanner/domains.html'


class RuleList(RestrictedListView):
    """Displays list of scanners."""
    model = RegexRule
    template_name = 'os2webscanner/rules.html'


class ReportList(RestrictedListView):
    """Displays list of scanners."""
    model = Scan
    template_name = 'os2webscanner/reports.html'

    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        if user.is_superuser:
            return self.model.objects.all()
        else:
            profile = user.get_profile()
            return self.model.objects.filter(scanner__organization=profile.organization)

# Create/Update/Delete Views.

class RestrictedCreateView(CreateView, LoginRequiredMixin):

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            user_profile = self.request.user.get_profile()
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization

        return super(RestrictedCreateView, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            self.fields.append('organization')

        result = super(RestrictedCreateView, self).get(self, request, *args,
                                                     **kwargs)
        return result


class ScannerCreate(RestrictedCreateView):
    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_name_scan', 'regex_rules']


class ScannerUpdate(UpdateView, LoginRequiredMixin):
    model = Scanner
    fields = ['name', 'schedule', 'whitelisted_names', 'domains',
              'do_cpr_scan', 'do_name_scan', 'regex_rules']


class ScannerDelete(DeleteView, LoginRequiredMixin):
    model = Scanner
    success_url = '/scanners/'


class DomainCreate(RestrictedCreateView):
    model = Domain
    fields = ['url', 'validation_status', 'validation_method',
              'exclusion_rules', 'sitemap']


class DomainUpdate(UpdateView, LoginRequiredMixin):
    model = Domain
    fields = ['url', 'validation_status', 'validation_method',
              'exclusion_rules', 'sitemap']


class DomainDelete(DeleteView, LoginRequiredMixin):
    model = Domain
    success_url = '/domains/'


class RuleCreate(RestrictedCreateView):
    model = RegexRule
    fields = ['name', 'match_string', 'description', 'sensitivity']


class RuleUpdate(UpdateView, LoginRequiredMixin):
    model = RegexRule


class RuleDelete(DeleteView, LoginRequiredMixin):
    model = RegexRule
    success_url = '/rules/'


# Reports stuff
class ReportDetails(DetailView, LoginRequiredMixin):
    """Display a detailed report."""
    model = Scan
    template_name = 'os2webscanner/report.html'
    context_object_name = "scan"

    def get_context_data(self, **kwargs):
        context = super(ReportDetails, self).get_context_data(**kwargs)
        all_matches = Match.objects.filter(
            scan=self.get_object()
        ).order_by('-sensitivity', 'url', 'matched_rule', 'matched_data')

        context['matches'] = all_matches
        return context
