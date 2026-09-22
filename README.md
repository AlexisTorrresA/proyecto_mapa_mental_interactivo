# Mapa Mental IA

Mapa conceptual interactivo de tecnología, IA, Machine Learning, NLP, visión, MLOps, cloud, ciberseguridad, robótica y computación cuántica.

Producción:

```text
https://mapa-mental-ia.alexistorreslabs.com
```

## Arquitectura

```text
GitHub main
  -> GitHub Actions
  -> ghcr.io/alexistorrresa/mapa-mental:main
  -> Y700 Deployment Manager
     -> postgres-main
        -> DB dedicada: mapa_mental_ia
     -> y700-mapa-mental
     -> Caddy
  -> mapa-mental-ia.alexistorreslabs.com
```

La app usa el PostgreSQL compartido del Y700. No levanta un PostgreSQL adicional.

## Datos

La fuente de verdad en producción son estas tablas:

- `map_nodes`: nodos y todo su contenido.
- `map_edges`: relaciones entre nodos.
- `map_meta`: metadatos de inicialización.

Los datos históricos que estaban definidos en Python siguen funcionando como **seed inicial** y como fallback para desarrollo/CI. Cuando la BD está vacía, la app los carga una única vez; después lee nodos y relaciones desde PostgreSQL.

## Editor de contenido

El editor permite:

- crear nodos;
- editar tipo, dominio, nombres, descripciones, año y URL;
- editar tags, subáreas, conceptos relacionados, funciones y ejemplos;
- crear/eliminar relaciones;
- eliminar nodos;
- descargar un respaldo JSON.

Como el sitio es público, el editor solo aparece si está configurado `MAPA_ADMIN_PASSWORD`.

En el Y700:

```bash
sudo y700-secret set MAPA_ADMIN_PASSWORD
sudo systemctl start y700-manager.service
```

No guardar la contraseña en GitHub ni en archivos versionados.

## PostgreSQL en Y700

El manifiesto declara:

```yaml
database:
  postgres: true
  name: mapa_mental_ia
```

El Y700 Deployment Manager se encarga de crear la base, usuario y contraseña y entregar `DATABASE_URL` al contenedor.

No configurar manualmente credenciales de `postgres-main` dentro de este repositorio.

## Desarrollo local

Sin `DATABASE_URL`, Streamlit arranca usando los datos incluidos en el código:

```bash
pip install -r requirements.txt
streamlit run mapa_mental.py
```

Para probar PostgreSQL localmente se puede definir `DATABASE_URL` según `.env.example`.

## Calidad

Antes de publicar una imagen, GitHub Actions ejecuta:

1. instalación de dependencias;
2. compilación Python;
3. tests con pytest;
4. smoke test real de Streamlit;
5. build Docker linux/amd64;
6. publicación en GHCR solo para `main`.

Los pull requests construyen la imagen para validarla, pero no la publican.

## Despliegue

`main` es la rama de producción. Después de un push exitoso, el Y700 reconciliará la nueva imagen automáticamente. Para forzarlo:

```bash
sudo systemctl start y700-manager.service
sudo journalctl -u y700-manager.service -n 100 --no-pager
```

Comprobaciones:

```bash
sudo docker ps --filter "name=y700-mapa-mental"
sudo docker logs --tail 100 y700-mapa-mental
```
