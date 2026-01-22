# Example YAML Recipe Configuration for XBloom MQTT Integration

This file demonstrates how to define XBloom coffee machine recipes in your Home Assistant `configuration.yaml`.

## Basic Configuration Example

```yaml
xbloom_mqtt:
  recipes:
    - name: "Morning Espresso"
      grind_size: 30
      rpm: 100
      bean_weight: 18.0
      total_water: 200
      cup_type: "omni_dripper"
      pours:
        - volume: 36
          temperature: 93
          pausing: 30
          flow_rate: 3.0
          pattern: "center"
        - volume: 164
          temperature: 93
          pausing: 0
          flow_rate: 3.5
          pattern: "spiral"

    - name: "Light Roast Pour Over"
      grind_size: 55
      rpm: 80
      bean_weight: 15.0
      total_water: 250
      cup_type: "omni_dripper"
      pours:
        - volume: 30
          temperature: 95
          pausing: 30
          flow_rate: 3.0
          pattern: "spiral"
        - volume: 110
          temperature: 95
          pausing: 0
          flow_rate: 3.2
          pattern: "spiral"
        - volume: 110
          temperature: 95
          pausing: 0
          flow_rate: 3.2
          pattern: "circular"

    - name: "Cold Brew Tea"
      grind_size: 100
      rpm: 60
      bean_weight: 10.0
      total_water: 300
      cup_type: "tea"
      pours:
        - volume: 300
          temperature: 75
          pausing: 0
          flow_rate: 3.0
          pattern: "center"
```

## Configuration Parameters

### Recipe Level Parameters

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `name` | ✓ | string | - | Unique name for the recipe |
| `grind_size` | | integer | 50 | Grind size (1-150) |
| `rpm` | | integer | 80 | Grinder speed in RPM (60-120) |
| `bean_weight` | | float | 15.0 | Weight of beans in grams (5.0-50.0) |
| `total_water` | | integer | 250 | Total water volume in ml (10-500) |
| `cup_type` | | string | "omni_dripper" | Cup type (see below) |
| `pours` | ✓ | list | - | List of pour steps |

### Cup Types

- `"x_pod"` - XBloom X Pod
- `"omni_dripper"` - Omni Dripper (default)
- `"other"` - Other cup type
- `"tea"` - Tea brewing

### Pour Step Parameters

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `volume` | ✓ | integer | - | Water volume for this pour in ml |
| `temperature` | ✓ | integer | - | Water temperature in °C (40-100) |
| `pausing` | | integer | 0 | Pause duration after pour in seconds |
| `flow_rate` | | float | 3.0 | Flow rate (3.0-3.5) |
| `pattern` | | string | "spiral" | Pour pattern (see below) |

### Pour Patterns

- `"center"` - Pour in the center
- `"circular"` - Circular pour pattern
- `"spiral"` - Spiral pour pattern (default)

## Important Notes

1. **YAML recipes override stored recipes**: If a YAML recipe has the same name as a recipe saved in persistent storage, the YAML version will be used.

2. **YAML recipes are not persisted**: YAML-defined recipes are loaded from your configuration file each time Home Assistant starts. They are never saved to the integration's persistent storage.

3. **Validation**: All parameters are validated when Home Assistant loads. If validation fails, an error will be logged and the recipe will be skipped.

4. **Multiple pours**: You can define as many pour steps as needed for your recipe. Each pour will be executed in sequence.

## Adding Recipes to Your Configuration

1. Open your Home Assistant `configuration.yaml` file
2. Add the `xbloom_mqtt:` section if it doesn't exist
3. Add your recipes under the `recipes:` key
4. Restart Home Assistant
5. Check the logs for successful recipe loading

## Example Log Output

When YAML recipes are loaded successfully, you should see log messages like:

```
DEBUG (MainThread) [custom_components.xbloom_mqtt.recipe_manager] Loaded YAML recipe: Morning Espresso
DEBUG (MainThread) [custom_components.xbloom_mqtt.recipe_manager] Loaded YAML recipe: Light Roast Pour Over
DEBUG (MainThread) [custom_components.xbloom_mqtt] Loaded 2 YAML recipes
```

## Using YAML Recipes

Once loaded, YAML recipes appear in the recipe selector alongside recipes saved through the Home Assistant interface. You can:

- Run them using the `xbloom_mqtt.run_recipe` service
- Select them in the recipe selector entity
- They will appear in any recipe list views

## Troubleshooting

If recipes don't load:

1. **Check YAML syntax**: Ensure your YAML is properly formatted
2. **Check logs**: Look for error messages in Home Assistant logs
3. **Verify parameters**: Ensure all required parameters are present and within valid ranges
4. **Restart**: Restart Home Assistant to reload the configuration
