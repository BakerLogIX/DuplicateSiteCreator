"""Static storefront builder using Jinja2 templates."""
from __future__ import annotations

from collections import defaultdict
from time import perf_counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import ProductRepository, StoreRepository
from core.metrics import get_collector
from core.storegen.theme_manager import get_theme_path


def _slugify(value: str) -> str:
    """Create a URL-friendly slug from the provided value."""

    return value.lower().replace(" ", "-")


def _group_products_by_category(products: Iterable) -> Dict[str, List]:
    """Group products by their category name with a stable order."""

    grouped: Dict[str, List] = defaultdict(list)
    for product in products:
        category = product.category or "Uncategorized"
        grouped[category].append(product)
    return dict(sorted(grouped.items(), key=lambda item: item[0].lower()))


def _render_template(env: Environment, template_name: str, output_path: Path, **context) -> None:
    """Render a template to the given output path."""

    template = env.get_template(template_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.render(**context), encoding="utf-8")


def build_store(
    store_id: int,
    output_dir: Path | str,
    theme_id: str = "default",
    db: Optional[Session] = None,
) -> Dict[str, Path]:
    """Generate a static storefront for the given store.

    Args:
        store_id: Identifier of the store to generate.
        output_dir: Directory where generated HTML files will be written.
        theme_id: Theme identifier to select templates. Defaults to ``"default"``.
        db: Optional SQLAlchemy session. If omitted, a new session is created.

    Returns:
        Mapping of generated page labels to their output paths.

    Raises:
        ValueError: If the store does not exist.
        FileNotFoundError: If the requested theme cannot be located.
    """

    session = db or SessionLocal()
    created_session = db is None
    try:
        collector = get_collector()
        store = StoreRepository(session).get_by_id(store_id)
        if not store:
            raise ValueError(f"Store with id {store_id} not found")

        product_repo = ProductRepository(session)
        products = product_repo.get_active_by_store(store_id)
        for product in products:
            if not getattr(product, "currency", None):
                product.currency = store.default_currency
        started_at = perf_counter()
        products_by_category = _group_products_by_category(products)
        categories = [
            {
                "name": name,
                "slug": _slugify(name),
                "count": len(category_products),
            }
            for name, category_products in products_by_category.items()
        ]

        theme_path = get_theme_path(theme_id)
        env = Environment(
            loader=FileSystemLoader(theme_path),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        output_root = Path(output_dir)
        output_root.mkdir(parents=True, exist_ok=True)

        generated_paths: Dict[str, Path] = {}
        _render_template(
            env,
            "home.html",
            output_root / "index.html",
            title="Home",
            store=store,
            categories=categories,
            products=products,
            products_by_category=products_by_category,
        )
        generated_paths["home"] = output_root / "index.html"

        for category_name, category_products in products_by_category.items():
            slug = _slugify(category_name)
            path = output_root / f"category-{slug}.html"
            _render_template(
                env,
                "category.html",
                path,
                title=category_name,
                store=store,
                category_name=category_name,
                products=category_products,
            )
            generated_paths[f"category:{slug}"] = path

        for product in products:
            path = output_root / f"product-{product.id}.html"
            _render_template(
                env,
                "product.html",
                path,
                title=product.name,
                store=store,
                product=product,
            )
            generated_paths[f"product:{product.id}"] = path

        collector.increment("storegen.pages_generated", len(generated_paths), store_id=store_id)
        collector.observe("storegen.products_rendered", len(products), store_id=store_id)
        collector.observe("storegen.duration_seconds", perf_counter() - started_at, store_id=store_id)
        return generated_paths
    finally:
        if created_session:
            session.close()
