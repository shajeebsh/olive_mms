import json

from django.http import HttpResponse


class HTMXPartialMixin:
    """Render a slim partial instead of the full page for HTMX requests.

    Lets a list/index page refresh itself from the same URL after a change
    (htmx adds ``HX-Request: true`` automatically).
    """

    partial_template = None

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true" and self.partial_template:
            return [self.partial_template]
        return super().get_template_names()


class HTMXModalFormMixin:
    """Render only the modal form partial for HTMX requests.

    On a successful HTMX submit, responds 204 and triggers ``closeModal`` +
    ``listChanged`` events so the page can hide the dialog and refresh.
    """

    modal_template = "includes/htmx_modal_form.html"
    modal_title = "Form"

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return [self.modal_template]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modal_title"] = self.get_modal_title()
        return ctx

    def get_modal_title(self):
        return self.modal_title

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("HX-Request") == "true":
            return HttpResponse(
                "",
                status=204,
                headers={"HX-Trigger": json.dumps({"closeModal": "", "listChanged": ""})},
            )
        return response


class HTMXDeleteMixin:
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("HX-Request") == "true":
            return HttpResponse(
                "",
                status=204,
                headers={"HX-Trigger": json.dumps({"listChanged": ""})},
            )
        return response
