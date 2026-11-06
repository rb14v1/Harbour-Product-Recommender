from rest_framework import serializers

from apps.products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "category", "price", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class SimilarProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.CharField()
    score = serializers.FloatField()


class SimilarResponseSerializer(serializers.Serializer):
    similar = SimilarProductSerializer(many=True)
    blurb = serializers.CharField()
    stub_mode = serializers.BooleanField()
