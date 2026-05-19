import stripe
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from apps.users.models import User

# Configuration Stripe avec clés de secours pour un fonctionnement immédiat en dev
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_51PzE4sP4LpXg2Q7q0placeholder_key')
webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

@login_required
def premium_page_view(request):
    """Affiche la page de souscription VIP premium avec le choix d'abonnement."""
    return render(request, 'marketing/premium.html', {
        'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', 'pk_test_51PzE4sP4LpXg2Q7qplaceholder_key')
    })

@login_required
def create_checkout_session_view(request):
    """Crée une session de paiement Stripe Checkout pour le statut PRO/VIP."""
    domain_url = request.build_absolute_uri('/')[:-1] # Enlever le slash final
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': '💎 DORO CAVIAR - Membre VIP Pro',
                        'description': 'Accès illimité à vie, suppression complète des publicités et des Ghost Clicks.',
                    },
                    'unit_amount': 999, # 9.99 EUR
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=domain_url + '/marketing/premium/success/',
            cancel_url=domain_url + '/marketing/premium/cancel/',
            metadata={
                'user_id': request.user.id
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def premium_success_view(request):
    """Page de succès suite au paiement Stripe. Modifie aussi le statut immédiatement en local pour le dev."""
    user = request.user
    user.is_pro = True
    user.save()
    return render(request, 'marketing/premium_success.html')

@login_required
def premium_cancel_view(request):
    """Page d'annulation de paiement."""
    return render(request, 'marketing/premium_cancel.html')

@csrf_exempt
def stripe_webhook_view(request):
    """Webhook de Stripe pour valider le paiement asynchronement."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        if sig_header and webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # Fallback dev : parser directement le JSON
            event = json.loads(payload)
    except Exception as e:
        return HttpResponse(status=400)

    # Gérer la complétion de session de paiement
    event_type = event.get('type') if isinstance(event, dict) else event.type
    if event_type == 'checkout.session.completed':
        session = event.get('data', {}).get('object') if isinstance(event, dict) else event.data.object
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user.is_pro = True
                user.save()
                print(f"L'utilisateur {user.username} a été promu PRO VIP via Stripe Webhook !")
            except User.DoesNotExist:
                print(f"Utilisateur ID {user_id} introuvable lors de l'exécution du Webhook.")

    return HttpResponse(status=200)
