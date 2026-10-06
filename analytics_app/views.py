from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from emergencies.models import EmergencyRequest
from relief.models import Resource, Donation, Hospital, Shelter, Responder
from gdacs_integration.models import GDACSEvent
from .algorithms import compute_fair_resource_allocation, get_response_time_analytics

@login_required
def analytics_dashboard(request):
    """
    Dedicated Analytics & Operations Research Dashboard:
    - Emergency Priority Score distribution & breakdown
    - Resource Allocation formula implementation
    - Response Time analytics
    """
    # 1. Priority Score Statistics & Classification distribution
    all_requests = EmergencyRequest.objects.all()
    priority_counts = {
        'Critical': all_requests.filter(priority_classification='Critical').count(),
        'High': all_requests.filter(priority_classification='High').count(),
        'Medium': all_requests.filter(priority_classification='Medium').count(),
        'Low': all_requests.filter(priority_classification='Low').count(),
    }

    # Sample active requests with their exact 5 component parameters
    scored_requests = all_requests.order_by('-priority_score')[:15]

    # 2. Resource Allocation Algorithm calculation
    category_filter = request.GET.get('allocation_category')
    pool_override = request.GET.get('pool_size')
    try:
        pool_size = int(pool_override) if pool_override else None
    except ValueError:
        pool_size = None

    allocation_results = compute_fair_resource_allocation(
        category=category_filter,
        total_pool_override=pool_size
    )

    # 3. Response Time Analytics
    # Formula: Response Time = Resolved Time - Reported Time
    response_time_data = get_response_time_analytics()

    # 4. Inventory vs Need comparison
    resources = Resource.objects.all()
    available_categories = [c[0] for c in Resource.RESOURCE_CATEGORIES]

    return render(request, 'analytics/dashboard.html', {
        'priority_counts': priority_counts,
        'scored_requests': scored_requests,
        'allocation_results': allocation_results,
        'response_time_data': response_time_data,
        'resources': resources,
        'available_categories': available_categories,
        'selected_category': category_filter,
        'pool_size': pool_size,
    })
