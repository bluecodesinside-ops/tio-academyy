function catalogT(key, fallback) {
  return (window.TIO_I18N && window.TIO_I18N[key]) || fallback;
}

function catalogCsrfToken() {
  if (typeof getCookie === 'function') {
    const token = getCookie('csrftoken');
    if (token) return token;
  }
  const cookie = document.cookie.split(';').map(function (part) { return part.trim(); }).find(function (part) {
    return part.indexOf('csrftoken=') === 0;
  });
  if (cookie) return decodeURIComponent(cookie.split('=').slice(1).join('='));
  const input = document.querySelector('input[name=csrfmiddlewaretoken]');
  return input ? input.value : '';
}

async function postCatalogCheckout(url, payload) {
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': catalogCsrfToken(),
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify(Object.assign({ cancel_path: window.location.pathname }, payload)),
  });
  let data = {};
  try { data = await response.json(); } catch (e) { data = {}; }
  if (response.status === 401 && data.login_url) {
    window.location.href = data.login_url;
    return;
  }
  if (!response.ok || !data.ok) {
    const err = (data.errors && (data.errors.__all__ || Object.values(data.errors)[0])) || data.error || catalogT('paymentFailed', 'Payment failed.');
    throw new Error(Array.isArray(err) ? err[0] : String(err));
  }
  if (!data.checkout_url) throw new Error(catalogT('noCheckoutUrl', 'No checkout URL received'));
  window.location.href = data.checkout_url;
}

function bindCatalogPicker() {
  const root = document.getElementById('catalog-picker');
  if (!root) return;
  const productId = Number(root.getAttribute('data-product-id'));
  const kind = root.getAttribute('data-kind');
  const bundlePrice = Number(root.getAttribute('data-bundle-price') || 0);

  function selectedPackageInputs() {
    return Array.prototype.filter.call(
      root.querySelectorAll('input[name=package_ids]:not(:disabled)'),
      function (el) { return el.checked; }
    );
  }

  function refreshPhysioTotal() {
    const totalEl = root.querySelector('[data-selected-total]');
    if (!totalEl) return;
    const selected = selectedPackageInputs();
    let total = 0;
    selected.forEach(function (el) { total += Number(el.getAttribute('data-price') || 0); });
    totalEl.textContent = '€' + total.toFixed(2);
  }

  function selectedVideoInputs() {
    return Array.prototype.filter.call(
      root.querySelectorAll('input[name=media_asset_ids]:not(:disabled)'),
      function (el) { return el.checked; }
    );
  }

  function danceTiers() {
    return Array.prototype.map.call(root.querySelectorAll('[data-dance-tier]'), function (el) {
      return {
        count: Number(el.getAttribute('data-count') || 0),
        price: Number(el.getAttribute('data-price') || 0),
      };
    }).filter(function (tier) { return tier.count > 0 && tier.price > 0; });
  }

  function danceQuote(count) {
    const tiers = danceTiers();
    if (!count || !tiers.length) return 0;
    let unit = tiers[0];
    tiers.forEach(function (tier) {
      if (tier.count < unit.count) unit = tier;
    });
    let best = unit.price * count;
    tiers.forEach(function (tier) {
      if (count <= tier.count && tier.price <= best) best = tier.price;
    });
    return best;
  }

  function refreshDanceTotal() {
    const totalEl = root.querySelector('[data-selected-total]');
    if (!totalEl || kind !== 'dance_videos') return;
    totalEl.textContent = '€' + danceQuote(selectedVideoInputs().length).toFixed(2);
  }

  function refreshVideoCardState() {
    root.querySelectorAll('.catalog-picker__item--video').forEach(function (item) {
      const input = item.querySelector('input[type=checkbox]');
      item.classList.toggle('is-selected', !!(input && input.checked));
    });
  }

  function refreshTotals() {
    refreshPhysioTotal();
    refreshDanceTotal();
    refreshVideoCardState();
  }
  root.addEventListener('change', refreshTotals);
  const selectAll = root.querySelector('[data-select-all]');
  const selectNone = root.querySelector('[data-select-none]');
  if (selectAll) {
    selectAll.addEventListener('click', function () {
      root.querySelectorAll('input[type=checkbox]:not(:disabled)').forEach(function (el) { el.checked = true; });
      refreshTotals();
    });
  }
  if (selectNone) {
    selectNone.addEventListener('click', function () {
      root.querySelectorAll('input[type=checkbox]:not(:disabled)').forEach(function (el) { el.checked = false; });
      refreshTotals();
    });
  }

  const buySelected = root.querySelector('[data-buy-selected]');
  if (buySelected) {
    buySelected.addEventListener('click', async function (event) {
      const ids = selectedPackageInputs().map(function (el) { return Number(el.value); });
      if (!ids.length) {
        alert(catalogT('selectPackage', 'Select at least one package.'));
        return;
      }
      const button = event.currentTarget;
      const original = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      try {
        await postCatalogCheckout('/api/catalog/checkout/packages/', {
          product_id: productId,
          package_ids: ids,
        });
      } catch (err) {
        alert(err.message || catalogT('paymentFailed', 'Payment failed.'));
        button.disabled = false;
        button.innerHTML = original;
      }
    });
  }

  const buyAll = root.querySelector('[data-buy-all]');
  if (buyAll) {
    buyAll.addEventListener('click', async function (event) {
      const button = event.currentTarget;
      const original = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      try {
        await postCatalogCheckout('/api/catalog/checkout/bundle/', { product_id: productId });
      } catch (err) {
        alert(err.message || catalogT('paymentFailed', 'Payment failed.'));
        button.disabled = false;
        button.innerHTML = original;
      }
    });
  }

  const buySelectedVideos = root.querySelector('[data-buy-selected-videos]');
  if (buySelectedVideos) {
    buySelectedVideos.addEventListener('click', async function (event) {
      const ids = selectedVideoInputs().map(function (el) { return Number(el.value); });
      if (!ids.length) {
        alert(catalogT('selectVideo', 'Select at least one video.'));
        return;
      }
      const button = event.currentTarget;
      const original = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      try {
        await postCatalogCheckout('/api/catalog/checkout/dance/', {
          product_id: productId,
          media_asset_ids: ids,
        });
      } catch (err) {
        alert(err.message || catalogT('paymentFailed', 'Payment failed.'));
        button.disabled = false;
        button.innerHTML = original;
      }
    });
  }

  refreshTotals();
}

function bindBuyPacketButtons() {
  document.querySelectorAll('[data-buy-packet]').forEach(function (button) {
    button.addEventListener('click', async function (event) {
      const packageId = Number(button.getAttribute('data-package-id'));
      if (!packageId) {
        alert(catalogT('packetNotReady', 'This packet is not ready for checkout yet.'));
        return;
      }
      const original = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      try {
        await postCatalogCheckout('/api/catalog/checkout/package/', { package_id: packageId });
      } catch (err) {
        alert(err.message || catalogT('paymentFailed', 'Payment failed.'));
        button.disabled = false;
        button.innerHTML = original;
      }
    });
  });
}

function bindPacketPager() {
  const root = document.querySelector('.catalog-picker--packets');
  if (!root) return;
  const items = Array.prototype.slice.call(root.querySelectorAll('[data-packet-item]'));
  const pageSize = Number(root.getAttribute('data-page-size') || 5);
  const pager = root.querySelector('.packet-pager');
  const prevBtn = root.querySelector('[data-packet-prev]');
  const nextBtn = root.querySelector('[data-packet-next]');
  const status = root.querySelector('[data-packet-status]');
  if (!items.length || items.length <= pageSize) return;
  if (pager) pager.hidden = false;

  let page = 0;
  const pageCount = Math.ceil(items.length / pageSize);

  function render() {
    const start = page * pageSize;
    const end = start + pageSize;
    items.forEach(function (item, index) {
      item.hidden = index < start || index >= end;
    });
    if (status) status.textContent = (page + 1) + ' / ' + pageCount;
    if (prevBtn) prevBtn.disabled = page === 0;
    if (nextBtn) nextBtn.disabled = page >= pageCount - 1;
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', function () {
      if (page > 0) {
        page -= 1;
        render();
        root.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', function () {
      if (page < pageCount - 1) {
        page += 1;
        render();
        root.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }
  render();
}

document.addEventListener('DOMContentLoaded', function () {
  bindCatalogPicker();
  bindBuyPacketButtons();
  bindPacketPager();
});
