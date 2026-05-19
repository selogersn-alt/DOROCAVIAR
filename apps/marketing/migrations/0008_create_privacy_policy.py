from django.db import migrations

def create_privacy_policy_page(apps, schema_editor):
    Page = apps.get_model('marketing', 'Page')
    if not Page.objects.filter(slug='confidentialite').exists():
        Page.objects.create(
            title="Charte de Confidentialité",
            slug="confidentialite",
            content="""<h2>1. Collecte des informations</h2>
<p>Nous collectons des informations lorsque vous créez un compte sur notre site DORO CAVIAR, aimez des vidéos, participez à des discussions ou naviguez sur les pages.</p>

<h2>2. Utilisation des informations</h2>
<p>Toutes les informations que nous recueillons auprès de vous peuvent être utilisées pour :</p>
<ul>
    <li>Personnaliser votre expérience de navigation et répondre à vos besoins individuels via notre algorithme de recommandation.</li>
    <li>Fournir un contenu publicitaire adapté et des recommandations fluides.</li>
    <li>Améliorer les performances de notre lecteur vidéo et l'ergonomie générale du site.</li>
    <li>Gérer les conversations privées entre utilisateurs.</li>
</ul>

<h2>3. Protection des données personnelles</h2>
<p>DORO CAVIAR s'engage à assurer la sécurité de vos informations personnelles. Vos données ne sont ni vendues, ni louées, ni échangées avec des tiers sous aucun prétexte sans votre accord préalable.</p>

<h2>4. Cookies & Mesures de Navigation</h2>
<p>Nous utilisons des cookies locaux pour :</p>
<ul>
    <li>Conserver votre session utilisateur active.</li>
    <li>Mémoriser votre historique de lecture et vos goûts afin d'adapter nos suggestions.</li>
    <li>Détecter la vitesse de votre bande passante pour optimiser le flux de lecture de notre lecteur vidéo.</li>
</ul>

<h2>5. Droit d'accès et de suppression</h2>
<p>Vous disposez d'un droit permanent d'accès, de rectification et de suppression des données vous concernant. Vous pouvez à tout moment exercer ce droit en modifiant votre profil ou en prenant contact avec nos équipes.</p>

<h2>6. Consentement</h2>
<p>En naviguant sur DORO CAVIAR, vous acceptez pleinement et sans réserve notre politique de confidentialité.</p>""",
            content_format="HTML",
            is_published=True
        )

def remove_privacy_policy_page(apps, schema_editor):
    Page = apps.get_model('marketing', 'Page')
    Page.objects.filter(slug='confidentialite').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0007_page_content_format_alter_page_content'),
    ]

    operations = [
        migrations.RunPython(create_privacy_policy_page, reverse_code=remove_privacy_policy_page),
    ]
