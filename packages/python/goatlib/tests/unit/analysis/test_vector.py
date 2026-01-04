#!/usr/bin/env python3
"""
Comprehensive test script for join functionality.
Tests multiple scenarios with the generated test data.
"""

import sys
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from goatlib.analysis.data_management.join import JoinTool
from goatlib.analysis.schemas.vector import (
    AttributeRelationship,
    FieldStatistic,
    JoinOperationType,
    JoinParams,
    JoinType,
    MultipleMatchingRecordsType,
    SortConfiguration,
    SortOrder,
    SpatialRelationshipType,
    StatisticOperation,
)


def test_one_to_many_join() -> bool:
    """Test one-to-many join (products with multiple reviews)."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"
    output_path = "/tmp/test_one_to_many.parquet"

    params = JoinParams(
        target_path=str(test_data_dir / "products.parquet"),
        join_path=str(test_data_dir / "reviews.parquet"),
        output_path=output_path,
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(target_field="product_id", join_field="product_id")
        ],
        join_operation=JoinOperationType.one_to_many,
        join_type=JoinType.inner,
    )

    print("🧪 Testing one-to-many join...")
    tool = JoinTool()
    tool.run(params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE result AS SELECT * FROM read_parquet('{output_path}')")

    count_result = con.execute("SELECT COUNT(*) FROM result").fetchone()
    print(f"✓ One-to-many join: {count_result[0]} records")

    # Check laptop reviews (should be 3)
    laptop_count = con.execute(
        "SELECT COUNT(*) FROM result WHERE product_id = 101"
    ).fetchone()
    print(f"✓ Laptop reviews: {laptop_count[0]} (expected: 3)")

    return count_result[0] == 9 and laptop_count[0] == 3


def test_statistical_aggregation() -> bool:
    """Test statistical aggregation join."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"
    output_path = "/tmp/test_stats.parquet"

    params = JoinParams(
        target_path=str(test_data_dir / "regions.parquet"),
        join_path=str(test_data_dir / "sales_data.parquet"),
        output_path=output_path,
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(target_field="region_code", join_field="region_code")
        ],
        join_operation=JoinOperationType.one_to_one,
        multiple_matching_records=MultipleMatchingRecordsType.calculate_statistics,
        field_statistics=[
            FieldStatistic(
                field="sales_amount",
                operations=[
                    StatisticOperation.sum,
                    StatisticOperation.count,
                    StatisticOperation.mean,
                ],
            ),
            FieldStatistic(
                field="units_sold",
                operations=[StatisticOperation.sum, StatisticOperation.max],
            ),
        ],
        join_type=JoinType.left,
    )

    print("🧪 Testing statistical aggregation...")
    tool = JoinTool()
    tool.run(params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE result AS SELECT * FROM read_parquet('{output_path}')")

    # Check North region statistics
    north_stats = con.execute(
        "SELECT sales_amount_sum, sales_amount_count, units_sold_sum FROM result WHERE region_code = 'NORTH'"
    ).fetchone()

    print(
        f"✓ North region - Sales sum: ${north_stats[0]:,.2f}, Count: {north_stats[1]}, Units: {north_stats[2]}"
    )

    # Verify expected values (North has 4 sales records, but 1 has NULL sales_amount)
    expected_sum = 1500.50 + 2200.75 + 1800.00  # Excludes NULL
    success = (
        abs(float(north_stats[0]) - expected_sum) < 0.01
        and north_stats[1] == 3  # Count excludes NULL
        and north_stats[2] == 95
    )  # 25+18+22+30 units

    return success


def test_multiple_field_join() -> bool:
    """Test join with multiple attribute relationships."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"
    output_path = "/tmp/test_multi_field.parquet"

    params = JoinParams(
        target_path=str(test_data_dir / "employees.parquet"),
        join_path=str(test_data_dir / "salary_bands.parquet"),
        output_path=output_path,
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(target_field="department", join_field="department"),
            AttributeRelationship(target_field="level", join_field="level"),
        ],
        join_operation=JoinOperationType.one_to_one,
        multiple_matching_records=MultipleMatchingRecordsType.first_record,
        sort_configuration=SortConfiguration(
            field="min_salary", sort_order=SortOrder.ascending
        ),
        join_type=JoinType.inner,
    )

    print("🧪 Testing multiple field join...")
    tool = JoinTool()
    tool.run(params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE result AS SELECT * FROM read_parquet('{output_path}')")

    count_result = con.execute("SELECT COUNT(*) FROM result").fetchone()

    # Check John Doe (Engineering, Senior)
    john_salary = con.execute(
        "SELECT join_min_salary, join_max_salary FROM result WHERE first_name = 'John' AND last_name = 'Doe'"
    ).fetchone()

    print(f"✓ Multiple field join: {count_result[0]} employees matched")
    print(f"✓ John Doe salary range: ${john_salary[0]:,} - ${john_salary[1]:,}")

    return count_result[0] == 6 and john_salary[0] == 85000


def test_inner_vs_left_join() -> bool:
    """Test difference between inner and left joins."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"

    # Inner join
    inner_params = JoinParams(
        target_path=str(test_data_dir / "customers.parquet"),
        join_path=str(test_data_dir / "categories.parquet"),
        output_path="/tmp/test_inner.parquet",
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(
                target_field="category_code", join_field="category_code"
            )
        ],
        join_operation=JoinOperationType.one_to_one,
        multiple_matching_records=MultipleMatchingRecordsType.first_record,
        sort_configuration=SortConfiguration(
            field="category_name", sort_order=SortOrder.ascending
        ),
        join_type=JoinType.inner,
    )

    # Left join
    left_params = JoinParams(
        target_path=str(test_data_dir / "customers.parquet"),
        join_path=str(test_data_dir / "categories.parquet"),
        output_path="/tmp/test_left.parquet",
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(
                target_field="category_code", join_field="category_code"
            )
        ],
        join_operation=JoinOperationType.one_to_one,
        multiple_matching_records=MultipleMatchingRecordsType.first_record,
        sort_configuration=SortConfiguration(
            field="category_name", sort_order=SortOrder.ascending
        ),
        join_type=JoinType.left,
    )

    print("🧪 Testing inner vs left join...")

    inner_tool = JoinTool()
    inner_tool.run(inner_params)

    left_tool = JoinTool()
    left_tool.run(left_params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")

    con.execute(
        "CREATE TABLE inner_result AS SELECT * FROM read_parquet('/tmp/test_inner.parquet')"
    )
    con.execute(
        "CREATE TABLE left_result AS SELECT * FROM read_parquet('/tmp/test_left.parquet')"
    )

    inner_count = con.execute("SELECT COUNT(*) FROM inner_result").fetchone()
    left_count = con.execute("SELECT COUNT(*) FROM left_result").fetchone()

    print(f"✓ Inner join: {inner_count[0]} records (excludes NULL categories)")
    print(f"✓ Left join: {left_count[0]} records (includes all customers)")

    return inner_count[0] == 6 and left_count[0] == 7


def test_spatial_intersects_join() -> bool:
    """Test spatial intersection join (points in polygons)."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"
    output_path = "/tmp/test_spatial_intersects.parquet"

    params = JoinParams(
        target_path=str(test_data_dir / "poi_points.parquet"),
        join_path=str(test_data_dir / "districts.parquet"),
        output_path=output_path,
        use_spatial_relationship=True,
        use_attribute_relationship=False,
        spatial_relationship=SpatialRelationshipType.intersects,
        join_operation=JoinOperationType.one_to_one,
        multiple_matching_records=MultipleMatchingRecordsType.first_record,
        sort_configuration=SortConfiguration(
            field="district_name", sort_order=SortOrder.ascending
        ),
        join_type=JoinType.left,
    )

    print("🧪 Testing spatial intersects join (POI in districts)...")
    tool = JoinTool()
    tool.run(params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE result AS SELECT * FROM read_parquet('{output_path}')")

    count_result = con.execute("SELECT COUNT(*) FROM result").fetchone()

    # Count POIs with district assignments
    poi_with_districts = con.execute(
        "SELECT COUNT(*) FROM result WHERE join_district_name IS NOT NULL"
    ).fetchone()

    print(f"✓ Spatial intersects join: {count_result[0]} total POIs")
    print(f"✓ POIs assigned to districts: {poi_with_districts[0]}")

    # Check specific POI assignment
    central_restaurant = con.execute(
        "SELECT name, join_district_name FROM result WHERE name = 'Central Restaurant'"
    ).fetchone()

    print(f"✓ Central Restaurant in: {central_restaurant[1]}")

    # Should have all 9 POIs, with 7 inside districts
    return count_result[0] == 9 and poi_with_districts[0] == 7


def test_spatial_distance_join() -> bool:
    """Test distance-based spatial join (schools near bus stops)."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"
    output_path = "/tmp/test_spatial_distance.parquet"

    params = JoinParams(
        target_path=str(test_data_dir / "schools.parquet"),
        join_path=str(test_data_dir / "bus_stops.parquet"),
        output_path=output_path,
        use_spatial_relationship=True,
        use_attribute_relationship=False,
        spatial_relationship=SpatialRelationshipType.within_distance,
        distance=2.0,  # Within 2 units
        distance_units="meters",  # Note: our test data uses unit coordinates
        join_operation=JoinOperationType.one_to_many,
        join_type=JoinType.inner,
    )

    print("🧪 Testing spatial distance join (schools near bus stops)...")
    tool = JoinTool()
    tool.run(params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE result AS SELECT * FROM read_parquet('{output_path}')")

    count_result = con.execute("SELECT COUNT(*) FROM result").fetchone()

    # Count unique schools with nearby bus stops
    schools_with_stops = con.execute(
        "SELECT COUNT(DISTINCT school_name) FROM result"
    ).fetchone()

    print(f"✓ School-bus stop matches within 2 units: {count_result[0]}")
    print(f"✓ Schools with nearby stops: {schools_with_stops[0]}")

    # Check specific school matches
    lincoln_stops = con.execute(
        "SELECT COUNT(*) FROM result WHERE school_name = 'Lincoln Elementary'"
    ).fetchone()

    print(f"✓ Bus stops near Lincoln Elementary: {lincoln_stops[0]}")

    # Should have 7 matches total based on our verification
    return count_result[0] == 7 and schools_with_stops[0] >= 3


def test_combined_spatial_and_attribute_join() -> bool:
    """Test combined spatial and attribute join."""
    output_path = "/tmp/test_combined_join.parquet"

    # First, create test data that has both spatial and attribute relationships
    import duckdb

    prep_con = duckdb.connect()
    prep_con.execute("INSTALL spatial; LOAD spatial;")

    # Create buildings with categories that match land zones
    prep_con.execute("""
    CREATE TABLE test_buildings AS SELECT * FROM VALUES
        (1, 'Office Building A', 'commercial', ST_Point(2, 2)),
        (2, 'House 1', 'residential', ST_Point(3, 2.5)),
        (3, 'Store 1', 'commercial', ST_Point(5, 3)),
        (4, 'House 2', 'residential', ST_Point(1.5, 6)),
        (5, 'Factory 1', 'industrial', ST_Point(8, 8))
    AS test_buildings(building_id, building_name, building_type, geometry)
    """)

    # Create zones that match both spatially and by attribute
    prep_con.execute("""
    CREATE TABLE test_zones AS SELECT * FROM VALUES
        ('ZONE_1', 'Downtown Commercial', 'commercial', 2.0,
         ST_GeomFromText('POLYGON((1 1, 6 1, 6 4, 1 4, 1 1))')),
        ('ZONE_2', 'Residential Area', 'residential', 1.0,
         ST_GeomFromText('POLYGON((0 5, 5 5, 5 8, 0 8, 0 5))')),
        ('ZONE_3', 'Mixed Use', 'commercial', 1.5,
         ST_GeomFromText('POLYGON((7 7, 12 7, 12 11, 7 11, 7 7))'))
    AS test_zones(zone_id, zone_name, zone_type, density, geometry)
    """)

    prep_con.execute(
        "COPY test_buildings TO '/tmp/test_buildings.parquet' (FORMAT PARQUET)"
    )
    prep_con.execute("COPY test_zones TO '/tmp/test_zones.parquet' (FORMAT PARQUET)")
    prep_con.close()

    params = JoinParams(
        target_path="/tmp/test_buildings.parquet",
        join_path="/tmp/test_zones.parquet",
        output_path=output_path,
        use_spatial_relationship=True,
        use_attribute_relationship=True,
        spatial_relationship=SpatialRelationshipType.intersects,
        attribute_relationships=[
            AttributeRelationship(target_field="building_type", join_field="zone_type")
        ],
        join_operation=JoinOperationType.one_to_one,
        multiple_matching_records=MultipleMatchingRecordsType.first_record,
        sort_configuration=SortConfiguration(
            field="zone_name", sort_order=SortOrder.ascending
        ),
        join_type=JoinType.inner,
    )

    print("🧪 Testing combined spatial and attribute join...")
    tool = JoinTool()
    tool.run(params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE result AS SELECT * FROM read_parquet('{output_path}')")

    count_result = con.execute("SELECT COUNT(*) FROM result").fetchone()

    # Show matches
    matches = con.execute(
        "SELECT building_name, join_zone_name FROM result ORDER BY building_name"
    ).fetchall()

    print(f"✓ Combined join matches: {count_result[0]}")
    for building, zone in matches:
        print(f"  {building} <-> {zone}")

    # Should have buildings that are both spatially within zones AND have matching types
    # Office Building A and Store 1 are commercial and in commercial zones
    return count_result[0] >= 2


def test_line_polygon_intersection() -> bool:
    """Test line-polygon intersection join (roads through zones)."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"
    output_path = "/tmp/test_line_polygon.parquet"

    params = JoinParams(
        target_path=str(test_data_dir / "roads.parquet"),
        join_path=str(test_data_dir / "land_zones.parquet"),
        output_path=output_path,
        use_spatial_relationship=True,
        use_attribute_relationship=False,
        spatial_relationship=SpatialRelationshipType.intersects,
        join_operation=JoinOperationType.one_to_many,
        join_type=JoinType.inner,
    )

    print("🧪 Testing line-polygon intersection join (roads through zones)...")
    tool = JoinTool()
    tool.run(params)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE result AS SELECT * FROM read_parquet('{output_path}')")

    count_result = con.execute("SELECT COUNT(*) FROM result").fetchone()

    # Count how many zones Main Street crosses
    main_street_zones = con.execute(
        "SELECT COUNT(*) FROM result WHERE road_name = 'Main Street'"
    ).fetchone()

    print(f"✓ Road-zone intersections: {count_result[0]}")
    print(f"✓ Zones crossed by Main Street: {main_street_zones[0]}")

    # Should have 10 intersections based on our verification
    return count_result[0] == 10 and main_street_zones[0] >= 2


def test_empty_results() -> bool:
    """Test joins that produce no matches and empty dataset handling."""
    test_data_dir = Path(__file__).parent.parent.parent / "data" / "vector"

    print("🧪 Testing empty results scenarios...")

    # Test 1: Join with no spatial matches (points far from polygons)
    import duckdb

    prep_con = duckdb.connect()
    prep_con.execute("INSTALL spatial; LOAD spatial;")

    # Create points that are far from any existing districts
    prep_con.execute("""
    CREATE TABLE remote_points AS SELECT * FROM VALUES
        (1, 'Remote Point 1', ST_Point(100, 100)),
        (2, 'Remote Point 2', ST_Point(200, 200)),
        (3, 'Remote Point 3', ST_Point(-100, -100))
    AS remote_points(point_id, name, geometry)
    """)

    prep_con.execute(
        "COPY remote_points TO '/tmp/remote_points.parquet' (FORMAT PARQUET)"
    )

    # Test spatial join with no matches
    params_no_matches = JoinParams(
        target_path="/tmp/remote_points.parquet",
        join_path=str(test_data_dir / "districts.parquet"),
        output_path="/tmp/test_no_matches.parquet",
        use_spatial_relationship=True,
        use_attribute_relationship=False,
        spatial_relationship=SpatialRelationshipType.intersects,
        join_operation=JoinOperationType.one_to_one,
        join_type=JoinType.inner,
    )

    tool = JoinTool()
    tool.run(params_no_matches)

    # Verify empty result
    check_con = duckdb.connect()
    check_con.execute("INSTALL spatial; LOAD spatial;")
    check_con.execute(
        "CREATE TABLE no_matches AS SELECT * FROM read_parquet('/tmp/test_no_matches.parquet')"
    )
    no_match_count = check_con.execute("SELECT COUNT(*) FROM no_matches").fetchone()

    print(f"✓ Inner join with no spatial matches: {no_match_count[0]} records")

    # Test 2: Left join with no matches (should preserve target records)
    params_left_no_matches = JoinParams(
        target_path="/tmp/remote_points.parquet",
        join_path=str(test_data_dir / "districts.parquet"),
        output_path="/tmp/test_left_no_matches.parquet",
        use_spatial_relationship=True,
        use_attribute_relationship=False,
        spatial_relationship=SpatialRelationshipType.intersects,
        join_operation=JoinOperationType.one_to_one,
        join_type=JoinType.left,
    )

    tool2 = JoinTool()  # Create new tool instance
    tool2.run(params_left_no_matches)

    check_con.execute(
        "CREATE TABLE left_no_matches AS SELECT * FROM read_parquet('/tmp/test_left_no_matches.parquet')"
    )
    left_no_match_count = check_con.execute(
        "SELECT COUNT(*) FROM left_no_matches"
    ).fetchone()
    null_join_count = check_con.execute(
        "SELECT COUNT(*) FROM left_no_matches WHERE join_district_name IS NULL"
    ).fetchone()

    print(f"✓ Left join with no spatial matches: {left_no_match_count[0]} records")
    print(f"✓ Records with NULL join values: {null_join_count[0]}")

    # Test 3: Empty target dataset (using attribute join to avoid geometry metadata issues)
    # Create empty table by copying structure from existing data
    prep_con.execute(
        f"CREATE TABLE empty_products AS SELECT * FROM read_parquet('{test_data_dir / 'products.parquet'}') WHERE FALSE"
    )

    prep_con.execute(
        "COPY empty_products TO '/tmp/empty_products.parquet' (FORMAT PARQUET)"
    )

    params_empty_target = JoinParams(
        target_path="/tmp/empty_products.parquet",
        join_path=str(test_data_dir / "reviews.parquet"),
        output_path="/tmp/test_empty_target.parquet",
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(target_field="product_id", join_field="product_id")
        ],
        join_operation=JoinOperationType.one_to_many,
        join_type=JoinType.left,
    )

    tool3 = JoinTool()  # Create new tool instance
    tool3.run(params_empty_target)

    check_con.execute(
        "CREATE TABLE empty_target_result AS SELECT * FROM read_parquet('/tmp/test_empty_target.parquet')"
    )
    empty_target_count = check_con.execute(
        "SELECT COUNT(*) FROM empty_target_result"
    ).fetchone()

    print(f"✓ Join with empty target dataset: {empty_target_count[0]} records")

    # Test 4: Empty join dataset (using attribute join)
    # Create empty table by copying structure from existing data
    prep_con.execute(
        f"CREATE TABLE empty_reviews AS SELECT * FROM read_parquet('{test_data_dir / 'reviews.parquet'}') WHERE FALSE"
    )

    prep_con.execute(
        "COPY empty_reviews TO '/tmp/empty_reviews.parquet' (FORMAT PARQUET)"
    )

    params_empty_join = JoinParams(
        target_path=str(test_data_dir / "products.parquet"),
        join_path="/tmp/empty_reviews.parquet",
        output_path="/tmp/test_empty_join.parquet",
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(target_field="product_id", join_field="product_id")
        ],
        join_operation=JoinOperationType.one_to_many,
        join_type=JoinType.left,
    )

    tool4 = JoinTool()  # Create new tool instance
    tool4.run(params_empty_join)

    check_con.execute(
        "CREATE TABLE empty_join_result AS SELECT * FROM read_parquet('/tmp/test_empty_join.parquet')"
    )
    empty_join_count = check_con.execute(
        "SELECT COUNT(*) FROM empty_join_result"
    ).fetchone()
    empty_join_nulls = check_con.execute(
        "SELECT COUNT(*) FROM empty_join_result WHERE join_rating IS NULL"
    ).fetchone()

    print(f"✓ Join with empty join dataset: {empty_join_count[0]} records")
    print(f"✓ Records with NULL join values: {empty_join_nulls[0]}")

    # Test 5: Attribute join with no matches
    prep_con.execute("""
    CREATE TABLE products_no_match AS SELECT * FROM VALUES
        (9999, 'Non-existent Product', 'electronics', 99.99)
    AS products_no_match(product_id, name, category, price)
    """)

    prep_con.execute(
        "COPY products_no_match TO '/tmp/products_no_match.parquet' (FORMAT PARQUET)"
    )

    params_attr_no_match = JoinParams(
        target_path="/tmp/products_no_match.parquet",
        join_path=str(test_data_dir / "reviews.parquet"),
        output_path="/tmp/test_attr_no_match.parquet",
        use_spatial_relationship=False,
        use_attribute_relationship=True,
        attribute_relationships=[
            AttributeRelationship(target_field="product_id", join_field="product_id")
        ],
        join_operation=JoinOperationType.one_to_many,
        join_type=JoinType.inner,
    )

    tool5 = JoinTool()  # Create new tool instance
    tool5.run(params_attr_no_match)

    check_con.execute(
        "CREATE TABLE attr_no_match AS SELECT * FROM read_parquet('/tmp/test_attr_no_match.parquet')"
    )
    attr_no_match_count = check_con.execute(
        "SELECT COUNT(*) FROM attr_no_match"
    ).fetchone()

    print(f"✓ Attribute join with no matches: {attr_no_match_count[0]} records")

    prep_con.close()
    check_con.close()

    # Verify all empty result scenarios
    return (
        no_match_count[0] == 0  # Inner join with no matches = empty
        and left_no_match_count[0] == 3
        and null_join_count[0] == 3  # Left join preserves target
        and empty_target_count[0] == 0  # Empty target = empty result
        and empty_join_count[0] == 5  # Products without reviews (5 products total)
        and empty_join_nulls[0] == 5  # Empty join dataset = NULLs
        and attr_no_match_count[0]
        == 0  # Attribute join no match = empty (no product 9999)
    )
