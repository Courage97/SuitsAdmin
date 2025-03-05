from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from decimal import Decimal
from django.db.models import Sum

from .models import Table, Reservation, BillSplit, TableInvoice
from sale.models import SaleItem, Sale
from .serializers import (
    TableSerializer, ReservationSerializer, 
    BillSplitSerializer, TableInvoiceSerializer, SaleItemSerializer
)
from .utils import generate_table_invoice

# 🟩 Table Views
class TableListCreateView(generics.ListCreateAPIView):
    """
    List and create tables.
    """
    queryset = Table.objects.all().order_by("table_number")
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter tables by status.
        """
        status = self.request.query_params.get("status")
        if status:
            return Table.objects.filter(status=status).order_by("table_number")
        return super().get_queryset()

class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific table.
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]


# 🟩 Reservation Views
from django.utils.timezone import now

class ReservationListCreateView(generics.ListCreateAPIView):
    """
    List and create reservations.
    """
    queryset = Reservation.objects.all().order_by("reservation_time")
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Set the user who created the reservation and prevent past reservations.
        """
        reservation_time = serializer.validated_data.get("reservation_time")
        if reservation_time and reservation_time < now():
            return Response({"error": "Reservation time must be in the future."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save(created_by=self.request.user)


class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific reservation.
    """
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]


# 🟩 Bill Split Views
class BillSplitCreateView(generics.CreateAPIView):
    """
    Split a bill for a completed sale.
    """
    serializer_class = BillSplitSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        sale_id = self.kwargs.get("sale_id")
        sale = get_object_or_404(Sale, id=sale_id)

        # Ensure the sale is completed
        if sale.status != "completed":
            return Response({"error": "Bill split is only allowed for completed sales."}, status=status.HTTP_400_BAD_REQUEST)

        total_paid = BillSplit.objects.filter(sale=sale).aggregate(total=Sum("amount_paid"))['total'] or Decimal("0.00")
        amount_requested = Decimal(str(request.data.get("amount_paid", 0)))

        # Prevent overpayments
        if total_paid + amount_requested > sale.total_amount:
            return Response({"error": "Total bill split exceeds sale total!"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate exchange rate
        payment_method = request.data.get("payment_method")
        exchange_rate = request.data.get("exchange_rate")
        if payment_method in ["usd", "eur", "bs"] and not exchange_rate:
            return Response({"error": f"Exchange rate required for {payment_method.upper()} payments."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the split
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sale=sale)

            # Check if fully paid and mark as settled
            total_paid += amount_requested
            if total_paid >= sale.total_amount:
                sale.status = "settled"
                sale.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BillSplitListView(generics.ListAPIView):
    """
    List all bill splits for a specific sale.
    """
    serializer_class = BillSplitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        sale_id = self.kwargs.get("sale_id")
        return BillSplit.objects.filter(sale_id=sale_id)


# 🟩 Kitchen and Bar Order Views
class KitchenOrderListView(generics.ListAPIView):
    """
    Fetch all orders assigned to the kitchen.
    """
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SaleItem.objects.filter(routed_to="kitchen").order_by("created_at")


class BarOrderListView(generics.ListAPIView):
    """
    Fetch all orders assigned to the bar.
    """
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SaleItem.objects.filter(routed_to="bar").order_by("created_at")


# 🟩 Table Invoice Generation
class TableInvoiceViewSet(viewsets.ViewSet):
    """
    Handle table invoice generation.
    """
    @action(detail=True, methods=['get'])
    def generate_invoice(self, request, pk=None):
        """
        Generate an invoice for a completed table session with SENIAT compliance.
        """
        table = get_object_or_404(Table, id=pk)
        
        # Check if there are completed sales for the table
        completed_sales = Sale.objects.filter(table=table, status="completed")
        if not completed_sales.exists():
            return Response({"error": "No completed sales for this table."}, status=status.HTTP_400_BAD_REQUEST)

        # Avoid regenerating invoices for the same sale
        existing_invoice = TableInvoice.objects.filter(table=table, sale__in=completed_sales).first()
        if existing_invoice:
            serializer = TableInvoiceSerializer(existing_invoice)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Generate new invoice
        try:
            invoice = generate_table_invoice(table.id)
            invoice.generate_control_code()  # Generate SENIAT control code
            invoice.calculate_total()        # Recalculate total amount

            # Handle empty invoices
            if invoice.total_amount == 0:
                return Response({"error": "Invoice is empty. No items ordered for this sale."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"Failed to generate invoice: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Return the invoice file URL
        serializer = TableInvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 🟩 Table Reset & Management
class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

    @action(detail=True, methods=['post'])
    def reset_table(self, request, pk=None):
        """
        Reset the table: mark as free, optionally close open sales.
        """
        table = self.get_object()

        # Prevent reset if there are unpaid sales
        unpaid_sales = Sale.objects.filter(table=table, status__in=["pending", "unpaid"])
        if unpaid_sales.exists():
            return Response({"error": "Cannot reset table with unpaid sales."}, status=status.HTTP_400_BAD_REQUEST)

        # Close any open sales
        open_sales = Sale.objects.filter(table=table, status='pending')
        open_sales.update(status='cancelled')

        # Reset table status
        table.mark_as_free()

        return Response({"message": f"Table {table.table_number} has been reset."}, status=status.HTTP_200_OK)
