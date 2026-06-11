"""Módulo de lógica de negocio: validaciones y orquestación del flujo de escaneo."""

from modules.database import barcode_exists, insert_record
from modules.barcode_reader import extract_barcode_info


# ---------- Validaciones ----------

def validate_barcode(codigo: str) -> tuple[bool, str]:
    codigo = (codigo or "").strip()
    if not codigo:
        return False, "El código de barras no puede estar vacío."
    if len(codigo) < 4:
        return False, "El código de barras es demasiado corto (mínimo 4 caracteres)."
    if len(codigo) > 128:
        return False, "El código de barras excede la longitud máxima permitida (128 caracteres)."
    return True, ""


def validate_weight(raw: str | float) -> tuple[bool, str, float | None]:
    try:
        value = float(str(raw).replace(",", ".").strip())
    except (ValueError, TypeError):
        return False, "El peso debe ser un número válido (ej: 1.5).", None

    if value <= 0:
        return False, "El peso debe ser mayor a cero.", None
    if value > 99_999:
        return False, "El peso ingresado parece inusualmente alto.", None
    return True, "", round(value, 4)


# ---------- Operaciones principales ----------

def process_new_scan(
    codigo: str,
    raw_peso: str | float,
    allow_duplicate: bool = False,
    producto_info: dict | None = None,
    foto_url: str = "",
) -> tuple[bool, str]:
    """
    Orquesta validación + guardado de un nuevo escaneo.
    producto_info: resultado de lookup_product() — se almacena tal cual en MongoDB.
    """
    ok_bc, err_bc = validate_barcode(codigo)
    if not ok_bc:
        return False, err_bc

    codigo = codigo.strip()

    if not allow_duplicate and barcode_exists(codigo):
        return False, (
            f"El código «{codigo}» ya existe en la base de datos. "
            "Activa «Permitir duplicados» si deseas agregarlo de todas formas."
        )

    ok_w, err_w, peso = validate_weight(raw_peso)
    if not ok_w:
        return False, err_w

    # Info técnica del código (tipo, longitud, país GS1, etc.)
    informacion = extract_barcode_info(codigo)

    # Nombre del producto proveniente de la API (vacío si no se encontró)
    nombre = ""
    if producto_info and producto_info.get("encontrado"):
        nombre = producto_info.get("nombre", "")
        # Enriquecer informacion con datos de API para facilitar consultas
        informacion["nombre_producto"] = nombre
        informacion["marca"] = producto_info.get("marca", "")
        informacion["fuente_api"] = producto_info.get("fuente", "")

    record_id = insert_record(
        codigo_barras=codigo,
        informacion=informacion,
        peso=peso,
        nombre_producto=nombre,
        producto_info=producto_info or {},
        foto_url=foto_url,
    )
    return True, record_id


def process_edit(
    record_id: str,
    codigo: str,
    raw_peso: str | float,
    nombre_producto: str = "",
    producto_info: dict | None = None,
) -> tuple[bool, str | list[str]]:
    """
    Valida y aplica cambios sobre un registro existente.
    Si el código cambió y se pasa producto_info, actualiza también la info de la API.
    """
    from modules.database import update_record  # noqa: PLC0415

    errors: list[str] = []

    ok_bc, err_bc = validate_barcode(codigo)
    if not ok_bc:
        errors.append(err_bc)

    ok_w, err_w, peso = validate_weight(raw_peso)
    if not ok_w:
        errors.append(err_w)

    if errors:
        return False, errors

    codigo = codigo.strip()

    if barcode_exists(codigo, exclude_id=record_id):
        return False, [
            f"El código «{codigo}» ya está asignado a otro registro. "
            "Cambia el código o revisa el duplicado."
        ]

    informacion = extract_barcode_info(codigo)
    if producto_info and producto_info.get("encontrado"):
        informacion["nombre_producto"] = producto_info.get("nombre", "")
        informacion["marca"] = producto_info.get("marca", "")
        informacion["fuente_api"] = producto_info.get("fuente", "")

    modified = update_record(
        record_id=record_id,
        codigo_barras=codigo,
        peso=peso,
        informacion=informacion,
        nombre_producto=nombre_producto,
        producto_info=producto_info,
    )

    if not modified:
        return False, ["No se realizaron cambios (los datos son idénticos al registro actual)."]

    return True, "Registro actualizado correctamente."
