import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rescuegrid_project.settings')

application = get_wsgi_application()

if 'VERCEL' in os.environ or os.getenv('VERCEL') == '1' or 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False)
        from core.models import User
        if User.objects.count() == 0:
            call_command('seed_data', interactive=False)
    except Exception as exc:
        print(f"Vercel DB Migration/Seed Exception: {exc}")

app = application
