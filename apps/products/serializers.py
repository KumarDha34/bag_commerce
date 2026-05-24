from rest_framework import serializers
from .models import Category, Bag
from django.utils.text import slugify


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for listing categories"""
    product_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'is_active', 'product_count']
    
    def get_product_count(self, obj):
        return obj.bags.filter(is_active=True).count()


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating categories"""
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'is_active']
    
    def validate_name(self, value):
        instance = self.instance
        
        if instance:
            if Category.objects.filter(name__iexact=value).exclude(id=instance.id).exists():
                raise serializers.ValidationError("Category with this name already exists")
        else:
            if Category.objects.filter(name__iexact=value).exists():
                raise serializers.ValidationError("Category with this name already exists")
        return value
    
    def create(self, validated_data):
        name = validated_data.get('name')
        slug = slugify(name)
        validated_data['slug'] = slug
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'name' in validated_data:
            name = validated_data['name']
            validated_data['slug'] = slugify(name)
        return super().update(instance, validated_data)


class BagSerializer(serializers.ModelSerializer):
    """Serializer for listing bags with multiple categories"""
    # This shows the full category data when reading
    categories_data = CategorySerializer(source='categories', many=True, read_only=True)
    category_names = serializers.SerializerMethodField()
    final_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Bag
        fields = [
            'id', 'categories', 'categories_data', 'category_names',
            'name', 'slug', 'description', 'price', 'discount_price',
            'final_price', 'discount_percentage', 'stock', 'sku',
            'image', 'is_active', 'featured', 'is_in_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'sku', 'created_at', 'updated_at']
    
    def get_category_names(self, obj):
        """Return comma-separated list of category names"""
        return ', '.join([cat.name for cat in obj.categories.all()])


class BagCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating bags with multiple categories"""
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories',  
        queryset=Category.objects.all(),
        many=True,
        write_only=True,
        required=True
    )
    
    class Meta:
        model = Bag
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discount_price',
            'stock', 'sku', 'image', 'is_active', 'featured', 
            'created_at', 'updated_at', 'category_ids'  # categories is NOT included
        ]        
        read_only_fields = ['id', 'slug', 'sku', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value
    
    def validate(self, data):
        # Validate discount price
        if data.get('discount_price') and data.get('price'):
            if data['discount_price'] >= data['price']:
                raise serializers.ValidationError({
                    'discount_price': 'Discount price must be less than regular price'
                })
        
        # Validate at least one category is selected (check via categories field after mapping)
        # The 'categories' field will be populated from 'category_ids' by DRF
        return data
    
    def create(self, validated_data):
        # Extract categories (this comes from category_ids via source='categories')
        categories = validated_data.pop('categories', [])
        
        # Generate slug from name if not provided
        if 'slug' not in validated_data or not validated_data['slug']:
            name = validated_data.get('name')
            validated_data['slug'] = slugify(name)
        
        # Generate SKU if not provided
        if 'sku' not in validated_data or not validated_data['sku']:
            import random
            import string
            validated_data['sku'] = f"BAG-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        
        # Create the bag
        bag = Bag.objects.create(**validated_data)
        
        # Set the many-to-many relationship
        bag.categories.set(categories)
        
        return bag
    
    def update(self, instance, validated_data):
        # Extract categories
        categories = validated_data.pop('categories', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update slug if name changed
        if 'name' in validated_data:
            instance.slug = slugify(instance.name)
        
        instance.save()
        
        # Update categories if provided
        if categories is not None:
            instance.categories.set(categories)
        
        return instance