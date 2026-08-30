"""============================================================ OPTIONAL CELERY STRATEGY MONITORING: latest stored data → dashboard Alert. ============================================================"""
from celery import shared_task
from core.models import Alert,MarketData,Strategy
@shared_task
def monitor_active_strategies():
    n=0
    for s in Strategy.objects.filter(is_active=True).prefetch_related('rules'):
        for r in s.rules.filter(is_active=True):
            last=MarketData.objects.filter(symbol=r.symbol).first()
            if last:Alert.objects.create(user=s.user,alert_type='strategy',title=f'{s.name} monitoring update',message=f'Latest {r.symbol} close: {last.close_price}'); n+=1
    return n
