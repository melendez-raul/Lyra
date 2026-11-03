# Lyra

Reproductor de música local con letras sincronizadas y colores que siguen a la portada. Hecho con Python y PySide6.

![Lyra reproduciendo una pista con letras sincronizadas](docs/screenshot.png)

## Características

- Biblioteca de archivos FLAC con portadas y metadatos.
- Letras sincronizadas (formato LRC), con autoscroll y clic para saltar a una línea.
- Acento de color derivado de la portada, con contraste garantizado (opcional).
- Tema editable: colores, transparencia y tipografías.

## Requisitos

- Python 3.11 o superior
- PySide6, mutagen y Pillow

```bash
pip install PySide6 mutagen Pillow
```

## Uso

Desde la carpeta que contiene `main.py`:

```bash
python main.py
```

En el primer arranque pide la carpeta de música. Se puede cambiar después en Configuración.

## Letras

Las letras se leen del tag `LYRICS` del FLAC, en formato LRC:

```
[00:12.50]Primera línea
[00:17.80]Segunda línea
```

Las líneas sin marca de tiempo se ignoran.

## Dónde guarda los datos

| Qué           | Dónde                                                                       |
| ------------- | --------------------------------------------------------------------------- |
| Configuración | `~/.config/Lyra/config.json` (Linux; la ruta equivalente en otros sistemas) |
| Base de datos | `<tu música>/Lyra/library.db`                                               |
| Portadas      | `<tu música>/Lyra/covers/`                                                  |

## Advertencias

**Haz una copia de seguridad de tu música antes del primer uso**, sobre todo si activas `structure_library`.

- **`structure_library` modifica tus archivos.** Está en `false` por defecto. Si lo activas (en `config.json`), el escaneo mueve y renombra las pistas a `Artista/Álbum/Título.flac` y elimina el tag `COMMENT` de cada FLAC. Con `false`, Lyra solo lee tus archivos y escribe únicamente dentro de `Lyra/`.
- **Activarlo después no reordena lo ya registrado.** Solo afecta a las pistas nuevas. Para aplicarlo a toda la biblioteca, borra la carpeta `Lyra/` y vuelve a escanear.
- **El escaneo sincroniza la base de datos con el disco.** Las pistas que ya no existen se borran de la biblioteca. Si la carpeta aparece vacía por un disco externo mal montado, se vaciará la base de datos (tus archivos no se tocan, pero tendrás que volver a escanear).
- **Con `structure_library` activo, las portadas se guardan junto a las pistas** (`cover.jpg`) y se borran cuando el álbum queda sin pistas.
- **Solo FLAC.** Otros formatos se ignoran.
- **El escaneo bloquea la interfaz.** Con bibliotecas grandes, la ventana puede quedar congelada unos segundos al arrancar o al cambiar de carpeta.
- **Sin migraciones.** Si cambia el esquema de la base de datos entre versiones, borra `Lyra/` (o solo `library.db` y `covers/`) y escanea de nuevo.
- **Los cambios de configuración se aplican al pulsar Guardar.** Cambiar la carpeta de la biblioteca recarga y detiene la reproducción.
- **Un `config.json` antiguo puede dar problemas.** Los colores se guardan como `#rrggbb`. Si el archivo tiene otro formato, bórralo y se regenera con los valores por defecto.
- **Fuentes:** Lyra no incluye fuentes. Usa Inter si está instalada y, si no, las del sistema. Para japonés, chino o coreano necesitas una fuente CJK (por ejemplo, `fonts-noto-cjk` en Linux).
- **Transparencia:** la ventana translúcida necesita un compositor activo. Sin él se ve opaca o con fondo negro.
- **Portadas grises o muy oscuras** no producen acento. En ese caso se usa el color primario del tema.

## Estructura

```
backend/        biblioteca (SQLite, tags, portadas), reproductor, controlador, config
frontend/       ventana, paneles, estilos (styles.py) y componentes
```
