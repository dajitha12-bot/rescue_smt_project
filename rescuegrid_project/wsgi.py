import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rescuegrid_project.settings')

application = get_wsgi_application()

if 'VERCEL' in os.environ or os.getenv('VERCEL') == '1' or 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False)
        from core.views import ensure_demo_data
        ensure_demo_data()
    except Exception as exc:
        print(f"Vercel DB Migration/Seed Exception: {exc}")

app = application
