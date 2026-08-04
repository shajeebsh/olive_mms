from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import HTMXDeleteMixin, HTMXModalFormMixin, HTMXPartialMixin
from core.utils import money

from .forms import CategoryForm, DistributionForm, ItemForm, StockMovementForm
from .models import Category, Item, StockLevel, StockMovement


class ItemListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Item
    template_name = "inventory/item_list.html"
    partial_template = "inventory/partials/item_list_content.html"
    context_object_name = "item_list"
    paginate_by = 25

    def get_queryset(self):
        queryset = Item.objects.select_related("category", "stock_level").order_by("name")
        q = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        low = self.request.GET.get("low", "").strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(category__name__icontains=q) | Q(unit__icontains=q)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if low:
            queryset = [item for item in queryset if item.is_low_stock]
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["low"] = self.request.GET.get("low", "")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["item_count"] = Item.objects.count()
        ctx["low_stock_count"] = sum(1 for item in Item.objects.select_related("stock_level") if item.is_low_stock)
        total_value = 0
        for item in Item.objects.select_related("stock_level"):
            total_value += item.quantity * item.price
        ctx["stock_value"] = money(total_value)
        ctx["month_movements"] = StockMovement.objects.filter(
            date__year=date.today().year, date__month=date.today().month
        ).count()
        return ctx


class ItemCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "inventory/item_form.html"
    success_url = reverse_lazy("inventory:index")

    def get_modal_title(self):
        return "Add item"


class ItemUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "inventory/item_form.html"
    success_url = reverse_lazy("inventory:index")

    def get_modal_title(self):
        return f"Edit {self.object.name}"


class ItemDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Item
    success_url = reverse_lazy("inventory:index")


class CategoryListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Category
    template_name = "inventory/category_list.html"
    partial_template = "inventory/partials/category_list_content.html"

    def get_queryset(self):
        return Category.objects.annotate(item_count=Count("items")).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category_count"] = Category.objects.count()
        return ctx


class CategoryCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:categories")

    def get_modal_title(self):
        return "Add category"


class CategoryUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:categories")

    def get_modal_title(self):
        return f"Edit {self.object.name}"


class CategoryDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("inventory:categories")


class StockMovementListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = StockMovement
    template_name = "inventory/movement_list.html"
    partial_template = "inventory/partials/movement_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = StockMovement.objects.select_related("item", "event", "recipient").order_by(
            "-date", "-id"
        )
        movement_type = self.request.GET.get("movement_type", "").strip()
        item = self.request.GET.get("item", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        if item:
            queryset = queryset.filter(item_id=item)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = Item.objects.filter(is_active=True).order_by("name")
        ctx["selected_type"] = self.request.GET.get("movement_type", "")
        ctx["selected_item"] = self.request.GET.get("item", "")
        ctx["date_from"] = self.request.GET.get("date_from", "")
        ctx["date_to"] = self.request.GET.get("date_to", "")
        ctx["in_total"] = money(
            self.object_list.filter(movement_type=StockMovement.MovementType.IN).aggregate(
                s=Sum("qty_change")
            )["s"]
        )
        ctx["out_total"] = money(
            self.object_list.filter(movement_type=StockMovement.MovementType.OUT).aggregate(
                s=Sum("qty_change")
            )["s"]
        )
        ctx["movement_count"] = self.object_list.count()
        return ctx


class StockMovementCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = "inventory/movement_form.html"
    success_url = reverse_lazy("inventory:movements")

    def get_initial(self):
        item_id = self.request.GET.get("item")
        return {"item": item_id} if item_id else {}

    def get_modal_title(self):
        return "Record stock movement"


class StockMovementDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = StockMovement
    success_url = reverse_lazy("inventory:movements")


class DistributionListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = StockMovement
    template_name = "inventory/distribution_list.html"
    partial_template = "inventory/partials/distribution_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = StockMovement.objects.filter(
            movement_type=StockMovement.MovementType.OUT
        ).select_related("item", "event", "recipient").order_by("-date", "-id")
        q = self.request.GET.get("q", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if q:
            queryset = queryset.filter(
                Q(recipient_name__icontains=q)
                | Q(recipient__full_name__icontains=q)
                | Q(item__name__icontains=q)
                | Q(purpose__icontains=q)
            )
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["date_from"] = self.request.GET.get("date_from", "")
        ctx["date_to"] = self.request.GET.get("date_to", "")
        ctx["distribution_total"] = money(
            self.object_list.aggregate(s=Sum("qty_change"))["s"]
        )
        ctx["distribution_count"] = self.object_list.count()
        ctx["recipient_count"] = self.object_list.filter(
            Q(recipient__isnull=False) | ~Q(recipient_name="")
        ).count()
        return ctx


class DistributionCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = StockMovement
    form_class = DistributionForm
    template_name = "inventory/distribution_form.html"
    success_url = reverse_lazy("inventory:distributions")

    def get_modal_title(self):
        return "Distribute stock"
