from .nash_bargaining import resolve_contested_field, Range, Resolution

def csp_negotiate(incident, agents):
    field_name = incident.get("field_name")
    
    if field_name == "min_security_level":
        # disjoint ranges — falls back to policy floor
        range_a = Range(0.30, 0.70)
        range_b = Range(0.80, 1.0)
        policy_floor = 0.75
        resolution = resolve_contested_field(range_a, range_b, 0.5, 0.5, policy_floor)
        return {"field": field_name, "value": resolution.value}
        
    return {"field": field_name, "value": 0.0}
