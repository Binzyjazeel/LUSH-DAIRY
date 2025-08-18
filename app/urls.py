from django.urls import path
from . import views




urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    
   path('logout/', views.logout_view, name='logout'),
    path('category/<int:category_id>/', views.products_by_category, name='products_by_category'),

    path('products/<int:product_id>/review/', views.add_review, name='add_review'),
   path('forgot-password/', views.forgot_password_request, name='forgot_password'),
    path("resend-reset-password-otp/", views.resend_reset_password_otp, name="resend_reset_password_otp"),
    path('verify-otp/', views.otp_verification, name='verify_otp'),
    
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('userproducts/', views.product_list, name='userproduct_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    
   path('profile/', views.profile_view, name='user_profile'),
    
 
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/upload-image/', views.update_profile_image, name='update_profile_image'),
    
   
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-email-otp/', views.resend_email_otp, name='resend_email_otp'),
    

    path('change-password/', views.change_password, name='change_password'),
    
    
 
    path('add-address/', views.add_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    

    
    path('order/<int:order_id>/', views.view_order, name='view_order'),
    path('set-default-address/<int:address_id>/', views.set_default_address, name='set_default_address'),

    
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'), 
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('cart/increment/', views.increment_cart, name='increment_cart'),
    path('cart/decrement/', views.decrement_cart, name='decrement_cart'),
    path('cart/remove/<int:cart_id>/', views.remove_cart_item, name='remove_cart_item'),
   
    path('checkout/', views.checkout_view, name='checkout'),
    path('add-address-checkout/', views.add_address_checkout, name='add_address_checkout'),


    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add-to-cart-from/<int:product_id>/', views.add_to_cart_from_wishlist, name='add_to_cart_from_wishlist'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-success/<str:order_id>/', views.order_success, name='order_success'),
    path('order/<str:order_id>/', views.order_detail, name='order_detail'), 
     path('order-list/', views.order_list, name='order_list'),
     path('profile-orders/', views.my_orders, name='my_orders'),

    path('order/cancel/<str:order_id>/', views.cancel_entire_order, name='cancel_entire_order'),
    path('order/item/cancel/<int:item_id>/', views.cancel_order_item, name='cancel_order_item'),

    path('invoice/<str:order_id>/', views.download_invoice, name='download_invoice'),
    path('order/return/<str:order_id>/', views.request_return, name='request_return'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('payment/handler/', views.payment_handler, name='payment_handler'),
    path('order-payment-success/<str:order_id>/', views.order_payment_success, name='order_payment_success'),

    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('start-payment/', views.razorpay_checkout_view, name='razorpay_checkout'),
     path('apply-coupon/', views.apply_coupon, name='apply_coupon'),  # ✅ Add this
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),

    




]

 

   






    



    

    
    



    




    


    