"""Store adapter registry.

Resolves the right adapter class for a store config row by:
  1. explicit `adapter_class` override in config
  2. `ec_platform` -> platform default adapter

Loading is lazy so an optional dependency (e.g. Playwright) that is not
installed does not break the import chain.
"""
from __future__ import annotations

import importlib
from typing import Type

from ..config import settings
from ..logging_setup import get_logger
from .base import AbstractStoreAdapter, StoreAdapterError

log = get_logger(__name__)

_PLATFORM_DEFAULTS: dict[str, str] = {
    "shopify": "ahc.stores.shopify_adapter.ShopifyAdapter",
    "magento": "ahc.stores.magento_adapter.MagentoAdapter",
    "woocommerce": "ahc.stores.woocommerce_adapter.WooCommerceAdapter",
    "generic": "ahc.stores.generic_adapter.GenericAdapter",
}


def _import_class(path: str) -> Type[AbstractStoreAdapter]:
    module_path, _, cls_name = path.rpartition(".")
    if not module_path:
        raise StoreAdapterError(f"Bad adapter_class path: {path!r}")
    module = importlib.import_module(module_path)
    if not hasattr(module, cls_name):
        raise StoreAdapterError(f"{path}: class not found")
    cls = getattr(module, cls_name)
    if not issubclass(cls, AbstractStoreAdapter):
        raise StoreAdapterError(f"{path}: not an AbstractStoreAdapter subclass")
    return cls


def adapter_for(store_config: dict) -> Type[AbstractStoreAdapter]:
    """Return the adapter class (not an instance) for one store config row."""
    explicit = store_config.get("adapter_class")
    if explicit:
        return _import_class(explicit)
    platform = store_config.get("ec_platform", "generic")
    path = _PLATFORM_DEFAULTS.get(platform)
    if not path:
        raise StoreAdapterError(
            f"Unknown ec_platform {platform!r} for store {store_config.get('slug')}"
        )
    return _import_class(path)


def get_adapter(
    store_config: dict,
    *,
    http_session=None,
    browser_page=None,
    dry_run: bool | None = None,
) -> AbstractStoreAdapter:
    """Instantiate an adapter for `store_config`.

    `dry_run` defaults to settings.dry_run_only (Chapter 9: real purchases
    disabled until explicitly approved).
    """
    cls = adapter_for(store_config)
    return cls(
        store_config,
        http_session=http_session,
        browser_page=browser_page,
        dry_run=settings.dry_run_only if dry_run is None else dry_run,
    )
