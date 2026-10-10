from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.template.response import TemplateResponse
from django.urls import path
from .models import Order, Item

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = 'admin/cart/order/change_list.html'

    def get_urls(self):
        custom_urls = [
            path(
                'top-purchasing-user/',
                self.admin_site.admin_view(self.top_purchasing_user_view),
                name = 'cart_order_top_purchasing_user',
            )
        ]
        return custom_urls + super().get_urls()

    def top_purchasing_user_view(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied
        
        rankings = (
            Item.objects.filter(
                order__user__is_staff = False,
                order__user__is_superuser=False,
            )
            .values('order__user_id', 'order__user__username')
            .annotate(movies_purchased=Sum('quantity'))
            .order_by(
                '-movies_purchased',
                'order__user__username',
                'order__user_id',
            )
        )
        top_user = rankings.first()

        leaders = (
            list(rankings.filter(
                movies_purchased=top_user['movies_purchased']
            ))
            if top_user else []
        )

        request.current_app = self.admin_site.name
        context = {
            **self.admin_site.each_context(request),
            'title': 'Top Purchasing User',
            'opts': self.model._meta,
            'leaders': leaders,
            'movies_purchased' : (
                top_user['movies_purchased'] if top_user else 0
            ),
        }

        return TemplateResponse(
            request,
            'admin/cart/order/top_purchasing_user.html',
            context,
        )

admin.site.register(Item)
