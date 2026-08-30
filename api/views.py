"""
============================================================
API ENDPOINTS
============================================================
Framework mapping: React → DRF endpoints → ORM/risk calculator/MATLAB bridge → JSON.
"""
from rest_framework import status,viewsets
from rest_framework.decorators import api_view,permission_classes,authentication_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from core.models import MarketData,Strategy,Backtest
from core.matlab_bridge import run_matlab_operation
from core.exceptions import MatlabUnavailable
from risk_management.calculators import calculate_position_size,calculate_stop_loss
from .serializers import MarketDataSerializer,StrategySerializer,BacktestSerializer
@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):return Response({'status':'ok','application':'MarketPulse','api':'Django REST Framework'})
@api_view(['GET'])
@permission_classes([AllowAny])
def market_latest(request):
    symbol=request.query_params.get('symbol','AAPL').strip().upper()
    try:limit=min(max(int(request.query_params.get('limit',60)),1),250)
    except ValueError:limit=60
    rows=list(MarketData.objects.filter(symbol=symbol).order_by('-date')[:limit]); rows.reverse(); return Response(MarketDataSerializer(rows,many=True).data)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def risk_position_size(request):
    try:return Response({'position_size':calculate_position_size(request.data['account_balance'],request.data['risk_percentage'],request.data['stop_loss_pct'],request.data['entry_price']),'stop_loss_price':calculate_stop_loss(request.data['entry_price'],request.data['stop_loss_pct'])})
    except (KeyError,TypeError,ValueError) as e:return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def matlab_risk(request):
    try:return Response(run_matlab_operation('risk',dict(request.data)))
    except MatlabUnavailable as e:return Response({'error':str(e)},status=status.HTTP_503_SERVICE_UNAVAILABLE)
class StrategyViewSet(viewsets.ModelViewSet):
    serializer_class=StrategySerializer; permission_classes=[IsAuthenticated]
    def get_queryset(self):return Strategy.objects.filter(user=self.request.user).order_by('-created_at')
    def perform_create(self,serializer):serializer.save(user=self.request.user)
class BacktestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=BacktestSerializer; permission_classes=[IsAuthenticated]
    def get_queryset(self):return Backtest.objects.filter(strategy__user=self.request.user).select_related('strategy').order_by('-created_at')
