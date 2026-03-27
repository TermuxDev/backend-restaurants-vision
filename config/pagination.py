from rest_framework.pagination import PageNumberPagination


class PaginationStandard(PageNumberPagination):
    page_size = 10
    page_size_query_param = "taille_page"
    max_page_size = 100
    page_query_param = "page"
