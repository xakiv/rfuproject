from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from rfu.models import Changeset, Territory, Node
from django.contrib.auth.models import User
from datetime import datetime, timedelta


from django.core.context_processors import csrf
from django.shortcuts import render_to_response

def check_param(request, param):
    if param not in request.GET:
        return False
    else:
        return True


def get_param(request, param):
    if param in request.GET:
        return request.GET[param]
    else:
        return None


def post_changeset(request):
    """Ce service permet de créer un nouveau changeset
    """
    # zone = "Indiquez une zone pour ce changeset"
    # if request.method == 'POST':
    #     # Get the posted form
    #     MyChangeSetForm = CsForm(request.POST)
    #
    #     if MyChangeSetForm.is_valid():
    #         zone = MyChangeSetForm.cleaned_data['zone']
    #         comment = MyChangeSetForm.cleaned_data['commentaire']
    # else:
    #     MyChangeSetForm = MyChangeSetForm()
    #
    # return render(request, 'cspost.html', {"zone": zone})
    print(request.POST['zone'])
    print(request.POST['ID'])
    return HttpResponseNotFound('<h1>Page not found</h1>')


def get_changeset(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed

    # RECUPERER les parametres de la requete GET
    # vérifier la présence des obligatoires
    # traiter les autres si présents. 
    # params obligatoire :
    # print ("--------------methode: {}".format(request.method))

    if not check_param(request, "zone"):
        # renvoyer erreur 400
        return HttpResponseBadRequest

    filters = {}

    # FILTRE TERRITOIRES: (param zone = metropole, antilles, guyane, reunion ou mayotte)
    zone = get_param(request, "zone")
    ter = get_object_or_404(Territory, old_schema_name="topology_" + zone)
    filters = {"cs_ter": ter}

    # FILTRE GE
    ge = get_param(request, "ge")
    if ge:
        my_ge = get_object_or_404(User, username=ge)
        filters.update({"cs_ge": my_ge})

    # FILTRE NOMBRE D'OBJETS: limite par defaut =10
    limit = get_param(request, 'limit')
    if limit is None:
        limit = 10
    print("limit: ", limit)

    # Filtre api dossier
    enr_api_dossier = get_param(request, "enr_api_dossier")
    if enr_api_dossier:
        filters.update({"cs_enr_api_dossier": enr_api_dossier})

    # Filtre Date ouverture
    date_ouvert = get_param(request, "ouvert_le")
    if date_ouvert:
        print("date_ouvert: ", date_ouvert)
        opendonbegin = datetime.strptime(date_ouvert, "%Y-%m-%d")
        opendonend = opendonbegin + timedelta(days=1)
        filters.update({"cs_ouvert_le__range": [opendonbegin, opendonend]})

    # Filtre Date de fermeture du changeset
    date_ferme = get_param(request, "ferme_le")
    if date_ferme:
        print("date_ferme: ", date_ferme)
        closedonbegin = datetime.strptime(date_ferme, "%Y-%m-%d")
        closedonend = closedonbegin + timedelta(days=1)
        filters.update({"cs_ferme_le__range": [closedonbegin, closedonend]})

    # Filtre Etat ouvert du changeset
    ouvert = get_param(request, "ouvert")
    # Demander à Matthieu les valeurs acceptables pour ce paramètre (yes, true, oui...)
    if ouvert and ouvert in ['true', 'True', 'Y', 'yes', 'Yes', 'Oui', 'oui']:
        print("ouvert: ", ouvert)
        filters.update({"cs_ferme_le__isnull": True})
    elif ouvert and ouvert in ['false', 'False', 'N', 'No', 'non', 'no', 'Non']:
        print("ouvert: ", ouvert)
        filters.update({"cs_ferme_le__isnull": False})
    cs = Changeset.objects.filter(**filters)
    ch = []
    for c in cs:
        if c.cs_ferme_le == None:
            ouvert = False
        else:
            ouvert = True
        if ge:
            res_ge = ge
        else:
            res_ge = c.cs_ge.username
        res = {
            "id": c.id,
            "ge": res_ge,
            "ouvert_le": c.cs_ouvert_le,
            "ferme_le": c.cs_ferme_le,
            "ouvert": ouvert,
            "commentaire": c.cs_commentaire,
            "enr_api_dossier": c.cs_enr_api_dossier,
            "link": "http://localhost/rfu/changeset/%s" % c.id
        }
        ch.append(res)

    response = {
        "changesets": ch
    }
    return JsonResponse(response)

# Fonction d'entrée depuis URL /changeset/
def on_changeset(request):
    if request.method == 'GET':
        return get_changeset(request)
    elif request.methode == 'POST':
        return post_changeset(request)
    else:
        return HttpResponseNotAllowed


def get_changeset_id(request, cs_zone, cs_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed  # Erreur405

    # Get zone from URL path
    zone = cs_zone

    if zone == 'm':
        f_zone = 'metropole'
    elif zone == 'a':
        f_zone = 'antille'
    elif zone == 'r':
        f_zone = 'reunion'
    elif zone == 'y':
        f_zone = 'mayotte'
    elif zone == 'g':
        f_zone = 'guyane'

    filters = {}
    ter_f = get_object_or_404(Territory, old_schema_name="topology_" + f_zone)
    filters = {"cs_ter": ter_f}

    cs_f = get_object_or_404(Changeset, id=cs_id)
    filters.update({"id": cs_f.id})


    # Lier les filtres
    my_cs = Changeset.objects.filter(**filters)
    if my_cs.count() == 0:
        return HttpResponseNotFound('<h1>Page not found: NO CHANGESET</h1>')
    else:
        tab_res = []
        for c in my_cs:
            print("---------------MYCS: {}".format(my_cs.values()))
            if c.cs_ferme_le == None:
                etat = True
            else:
                etat = False
            res = {
                "id": c.id,
                "ge": c.cs_ge.username,
                "ouvert_le": c.cs_ouvert_le,
                "ferme_le": c.cs_ferme_le,
                "ouvert": etat,
                "commentaire": c.cs_commentaire,
                "enr_api_dossier": c.cs_enr_api_dossier,
                "link": "http://localhost/rfu/changeset/{}{}".format(zone, c.id)
            }
            tab_res.append(res)
            response = {
                "changeset": res
            }
            return JsonResponse(response)

def get_sommet(request, sommet_id):
    """Ce service permet d’obtenir l’ensemble des versions d’un sommet RFU.
    """
    if request.method != 'GET':
        return HttpResponseNotAllowed  # Erreur405

    if sommet_id == None:
        #renvoyer erreur 400
        return HttpResponseBadRequest

    if not check_param(request, "zone"):
        return HttpResponseBadRequest
    filters = {}
    zone = get_param(request, "zone")
    print("----------zone: {}".format(zone))


    ter_f = get_object_or_404(Territory, old_schema_name="topology_" + zone)
    filters = {"node_ter": ter_f}

    node_f = get_object_or_404(Node, node_id=sommet_id)
    filters.update({"node_id":node_f.node_id})

    print("----------node: {}".format(node_f.node_id))

    sommet_f = Node.objects.filter(**filters)


    # Need VERSION



    # sommet_version = {
    #     "id_noeud"  #Identifiant unique du sommet RFU,
    #     "version" #Version du sommet RFU,
    #     "link" #URI de laversion du sommet RFU
    # }
    #
    # return JsonResponse(response)
