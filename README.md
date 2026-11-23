# Dietario para Home Assistant

Integración para ver en Home Assistant los menús de Dietario (web de menús semanales, repositorio privado) y usar su lista de la compra.

## Qué crea

| Entidad | Qué muestra |
|---|---|
| `sensor` Comida / Cena de hoy | Nombre del plato (atributos: resumen, qué preparar antes, etiquetas, puntuación) |
| `sensor` Comida / Cena de mañana | Igual, para mañana |
| `sensor` Para preparar hoy (mañana) | Nº de tareas de preparación para mañana (atributo `texto` con el detalle) |
| `sensor` Compra pendiente | Artículos sin marcar |
| `calendar` Menú | Todas las comidas (14:00) y cenas (21:00) de la semana como eventos |
| `todo` Lista de la compra | La lista de Dietario: añadir, marcar y borrar se sincroniza con la web |

Se actualiza cada 5 minutos (y al instante tras cambiar la lista de la compra desde Home Assistant).

## Instalación con HACS

1. HACS → ⋮ → **Repositorios personalizados** → pega la URL de este repositorio, categoría **Integración** → Añadir.
2. Busca **Dietario** en HACS → Descargar → reinicia Home Assistant.
3. En Dietario: **Familia → Integración con Home Assistant → Generar token** (solo lo ven los administradores).
4. En Home Assistant: Ajustes → Dispositivos y servicios → **Añadir integración → Dietario**.
   - URL: la de tu Dietario. Si Home Assistant está en la misma red, usa la interna (`http://192.168.68.27:3000`).
   - Token: el que acabas de generar.

### Instalación manual

Copia la carpeta `custom_components/dietario` a `/config/custom_components/` y reinicia.

## Panel de ejemplo (Lovelace)

```yaml
type: vertical-stack
cards:
  - type: entities
    title: 🍽️ Hoy
    entities:
      - entity: sensor.dietario_comida_de_hoy
      - entity: sensor.dietario_cena_de_hoy
      - entity: sensor.dietario_para_preparar_hoy_manana
  - type: markdown
    title: 🕒 Preparar hoy para mañana
    content: >
      {{ state_attr('sensor.dietario_para_preparar_hoy_manana', 'texto') or 'Nada que preparar 🎉' }}
  - type: calendar
    entities:
      - calendar.dietario_menu
    initial_view: listWeek
  - type: todo-list
    entity: todo.dietario_lista_de_la_compra
```
(Los nombres de entidad pueden variar según el nombre de tu familia: compruébalos en Ajustes → Entidades.)

## Automatización: aviso si hay que preparar algo

```yaml
automation:
  - alias: Dietario - preparar para mañana
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.dietario_para_preparar_hoy_manana
        above: 0
    action:
      - service: notify.mobile_app_tu_movil
        data:
          title: "Mañana: déjalo preparado"
          message: "{{ state_attr('sensor.dietario_para_preparar_hoy_manana', 'texto') }}"
```

## Seguridad

- El token da acceso a los menús y a la lista de la compra de **una familia** (no a cuentas ni contraseñas). Se puede revocar en Dietario.
- Dietario guarda solo el hash del token. Si lo pierdes, genera otro (el anterior deja de valer).
- Con HTTP en red local el token viaja sin cifrar dentro de tu LAN; si lo expones fuera, usa HTTPS.

## Logo

El icono y el logo están en `custom_components/dietario/brand/` (Home Assistant 2026.3+ los muestra en HACS y en la lista de integraciones).
