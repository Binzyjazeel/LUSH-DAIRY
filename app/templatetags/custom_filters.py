from django import template

register = template.Library()

@register.filter
def get_main_image(product):
    try:
        return product.images.first()
    except AttributeError:
        return None  
    

