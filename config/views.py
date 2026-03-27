from django.http import JsonResponse

def accueil(request):
    return JsonResponse({"message": "Bienvenue sur mon API , consulte ma documentation!"})