from . import views
from django.urls import path


urlpatterns = [
    path('accounts/login/', views.admin_login, name='admin_login'),
    path('accounts/logout/', views.admin_logout, name='admin_logout'),
    path('accounts/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('accounts/users/', views.user_list, name='user_list'),
    path('accounts/users/block/<int:user_id>/', views.toggle_block_user, name='toggle_block_user'),

    path('accounts/categories/', views.category_list, name='category_list'),
    path('accounts/categories/add/', views.category_add, name='category_add'),
    path('accounts/categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('accounts/categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('accounts/categories/clear-search/', views.category_clear_search, name='category_clear_search'),
    

    path('accounts/products/', views.product_list, name='product_list'),
    path('accounts/products/add/', views.add_product, name='add_product'),
    path('accounts/products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
     
    path('accounts/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('accounts/upload-image/', views.upload_image, name='upload_image'),

 
   
   path('accounts/add-variant/<int:product_id>/', views.add_variant, name='add_variant'),

   
    path('accounts/variant/edit/<int:variant_id>/', views.edit_variant, name='edit_variant'),
    path('accounts/variant/delete/<int:variant_id>/', views.delete_variant, name='delete_variant'),
   
      path('accounts/products/<int:product_id>/variants/', views.manage_variants, name='manage_variants'),


    path('admin-orders/', views.admin_order_list, name='admin_order_list'),
    path('admin-orders/<str:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-orders/<str:order_id>/change-status/', views.admin_change_order_status, name='admin_change_order_status'),
   
    
    path('accounts/stock/', views.inventory_list, name='inventory_list'),
    path('accounts/update-stock/<int:variant_id>/', views.update_stock, name='update_stock'),

    path('accounts/return/requests/', views.admin_return_requests, name='admin_return_requests'),
    path('accounts/return/approve/<int:request_id>/', views.approve_return_request, name='approve_return_request'),

    path('coupons/', views.coupon_list_view, name='coupon_list'),
    path('coupons/create/', views.create_coupon, name='create_coupon'),
   # urls.py
    path('accounts/coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),

    path('coupons/delete/<int:coupon_id>/', views.delete_coupon_view, name='delete_coupon'),
    path('accounts/sales-report/', views.sales_report, name='sales_report'),
    path('accounts/sales-report/pdf/', views.download_sales_report_pdf, name='download_sales_pdf'),
path('accounts/sales-report/excel/', views.download_sales_report_excel, name='download_sales_excel'),




]
