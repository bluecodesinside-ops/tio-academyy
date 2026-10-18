/**
 * Catalog admin configurators.
 * @typedef {{name:string, video_count:number, price:string, access_duration_days:number, access_duration_months?:number, discount_percent:string, is_active:boolean, id?:number}} PricingTierInput
 */

(function () {
  function csrfToken(root) {
    return (root && root.getAttribute('data-csrf')) ||
      (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value ||
      '';
  }

  function toast(panel, message, ok) {
    var el = panel.querySelector('.catalog-toast');
    if (!el) return;
    el.hidden = false;
    el.textContent = message;
    el.classList.toggle('is-ok', !!ok);
    el.classList.toggle('is-err', !ok);
  }

  function fieldError(input, on) {
    if (input) input.classList.toggle('catalog-field-error', !!on);
  }

  function validateTierRow(row) {
    var name = row.querySelector('[name=name]');
    var count = row.querySelector('[name=video_count]');
    var price = row.querySelector('[name=price]');
    var days = row.querySelector('[name=access_duration_days]');
    var months = row.querySelector('[name=access_duration_months]');
    var discount = row.querySelector('[name=discount_percent]');
    var ok = true;
    fieldError(name, !name.value.trim());
    if (!name.value.trim()) ok = false;
    var videoCount = Number(count.value);
    fieldError(count, !videoCount || videoCount < 1);
    if (!videoCount || videoCount < 1) ok = false;
    var priceVal = Number(price.value);
    fieldError(price, !(priceVal > 0));
    if (!(priceVal > 0)) ok = false;
    var dayVal = Number(days.value);
    var monthVal = Number(months && months.value);
    if (!dayVal && monthVal > 0) {
      days.value = String(monthVal * 30);
      dayVal = monthVal * 30;
    }
    fieldError(days, !(dayVal > 0));
    if (!(dayVal > 0)) ok = false;
    var disc = Number(discount.value || 0);
    fieldError(discount, disc < 0 || disc > 100);
    if (disc < 0 || disc > 100) ok = false;
    return ok;
  }

  function serializeTiers(panel) {
    var rows = panel.querySelectorAll('[data-tier-rows] tr');
    var tiers = [];
    var valid = true;
    rows.forEach(function (row, index) {
      if (!validateTierRow(row)) valid = false;
      var id = row.getAttribute('data-tier-id');
      tiers.push({
        id: id ? Number(id) : null,
        name: row.querySelector('[name=name]').value.trim(),
        video_count: Number(row.querySelector('[name=video_count]').value),
        price: row.querySelector('[name=price]').value,
        access_duration_days: Number(row.querySelector('[name=access_duration_days]').value),
        access_duration_months: Number(row.querySelector('[name=access_duration_months]').value || 0),
        discount_percent: row.querySelector('[name=discount_percent]').value || '0',
        is_active: row.querySelector('[name=is_active]').checked,
        display_order: index,
      });
    });
    return { tiers: tiers, valid: valid };
  }

  function postJson(url, body, csrf) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
      },
      body: JSON.stringify(body),
    }).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok && data.ok, data: data };
      });
    });
  }

  function bindTierForm(panel) {
    var tbody = panel.querySelector('[data-tier-rows]');
    panel.addEventListener('click', function (event) {
      if (event.target.matches('[data-add-tier]')) {
        var row = tbody.querySelector('tr');
        var clone = row.cloneNode(true);
        clone.removeAttribute('data-tier-id');
        clone.querySelectorAll('input').forEach(function (input) {
          if (input.type === 'checkbox') input.checked = true;
          else if (input.name === 'name') input.value = '';
          else if (input.name === 'video_count') input.value = '1';
          else if (input.name === 'price') input.value = '';
          else if (input.name === 'access_duration_days') input.value = '30';
          else if (input.name === 'access_duration_months') input.value = '1';
          else if (input.name === 'discount_percent') input.value = '0';
        });
        tbody.appendChild(clone);
      }
      if (event.target.matches('[data-remove-tier]')) {
        var rows = tbody.querySelectorAll('tr');
        if (rows.length === 1) return;
        event.target.closest('tr').remove();
      }
      if (event.target.matches('[data-save-tiers]')) {
        var payload = serializeTiers(panel);
        if (!payload.valid) {
          toast(panel, 'Fix the highlighted tier fields before saving.', false);
          return;
        }
        postJson(panel.getAttribute('data-save-url'), { tiers: payload.tiers }, csrfToken(panel.closest('.catalog-admin'))).then(function (result) {
          if (result.ok) {
            toast(panel, result.data.message || 'Pricing tiers saved.', true);
            if (result.data.tiers) {
              result.data.tiers.forEach(function (tier, i) {
                var row = tbody.querySelectorAll('tr')[i];
                if (row) row.setAttribute('data-tier-id', String(tier.id));
              });
            }
          } else {
            var err = (result.data.errors && (result.data.errors.__all__ || Object.values(result.data.errors)[0])) || 'Could not save tiers.';
            toast(panel, Array.isArray(err) ? err[0] : String(err), false);
          }
        }).catch(function () {
          toast(panel, 'Network error while saving tiers.', false);
        });
      }
    });
    panel.addEventListener('input', function (event) {
      var row = event.target.closest('tr');
      if (row) validateTierRow(row);
    });
  }

  function bindBundle(panel) {
    panel.addEventListener('click', function (event) {
      if (!event.target.matches('[data-save-bundle]')) return;
      var days = panel.querySelector('[name=access_duration_days]');
      var months = panel.querySelector('[name=access_duration_months]');
      var price = panel.querySelector('[name=bundle_price]');
      var enabled = panel.querySelector('[name=bundle_enabled]').checked;
      if (!Number(days.value) && Number(months.value) > 0) {
        days.value = String(Number(months.value) * 30);
      }
      fieldError(price, enabled && !(Number(price.value) > 0));
      if (enabled && !(Number(price.value) > 0)) {
        toast(panel, 'Bundle price must be greater than 0 when enabled.', false);
        return;
      }
      postJson(panel.getAttribute('data-save-url'), {
        bundle_enabled: enabled,
        bundle_title: panel.querySelector('[name=bundle_title]').value,
        bundle_price: price.value,
        access_duration_days: Number(days.value || 0),
        access_duration_months: Number(months.value || 0),
        expected_package_count: Number(panel.querySelector('[name=expected_package_count]').value || 15),
      }, csrfToken(panel.closest('.catalog-admin'))).then(function (result) {
        if (result.ok) toast(panel, result.data.message || 'Bundle saved.', true);
        else {
          var err = (result.data.errors && (result.data.errors.bundle_price || result.data.errors.__all__)) || 'Could not save bundle.';
          toast(panel, Array.isArray(err) ? err[0] : String(err), false);
        }
      }).catch(function () {
        toast(panel, 'Network error while saving bundle.', false);
      });
    });
  }

  function bindMapper(panel) {
    panel.addEventListener('click', function (event) {
      if (!event.target.matches('[data-save-mapper]')) return;
      var sessionIds = Array.prototype.map.call(
        panel.querySelectorAll('[name=session_ids]:checked'),
        function (el) { return Number(el.value); }
      );
      var assetIds = Array.prototype.map.call(
        panel.querySelectorAll('[name=media_asset_ids]:checked, [name=mapped_asset_ids]:checked'),
        function (el) { return Number(el.value); }
      );
      postJson(panel.getAttribute('data-save-url'), {
        package_id: Number(panel.getAttribute('data-package-id')),
        session_ids: sessionIds,
        media_asset_ids: assetIds,
      }, csrfToken(panel)).then(function (result) {
        if (result.ok) toast(panel, result.data.message || 'Videos mapped.', true);
        else {
          var err = (result.data.errors && Object.values(result.data.errors)[0]) || 'Could not map videos.';
          toast(panel, Array.isArray(err) ? err[0] : String(err), false);
        }
      }).catch(function () {
        toast(panel, 'Network error while mapping videos.', false);
      });
    });
  }

  function bindPhysioLayout(panel) {
    panel.addEventListener('click', function (event) {
      if (!event.target.matches('[data-save-physio-layout]')) return;
      var packages = [];
      var valid = true;
      panel.querySelectorAll('[data-physio-packages] tr[data-package-id]').forEach(function (row) {
        var title = row.querySelector('[name=title]');
        var price = row.querySelector('[name=individual_price]');
        fieldError(title, !title.value.trim());
        fieldError(price, !(Number(price.value) > 0));
        if (!title.value.trim() || !(Number(price.value) > 0)) valid = false;
        packages.push({
          id: Number(row.getAttribute('data-package-id')),
          title: title.value.trim(),
          individual_price: price.value,
        });
      });
      if (!valid) {
        toast(panel, 'Every package needs a name and a price greater than 0.', false);
        return;
      }
      var assignments = [];
      panel.querySelectorAll('[data-physio-videos] tr[data-session-id]').forEach(function (row) {
        var packageId = row.querySelector('[name=package_id]').value;
        if (packageId) {
          assignments.push({
            session_id: Number(row.getAttribute('data-session-id')),
            package_id: Number(packageId),
          });
        }
      });
      postJson(panel.getAttribute('data-save-url'), {
        packages: packages,
        assignments: assignments,
      }, csrfToken(panel.closest('.catalog-admin'))).then(function (result) {
        if (result.ok) toast(panel, result.data.message || 'Saved.', true);
        else {
          var err = (result.data.errors && (result.data.errors.__all__ || Object.values(result.data.errors)[0])) || 'Could not save.';
          toast(panel, Array.isArray(err) ? err[0] : String(err), false);
        }
      }).catch(function () {
        toast(panel, 'Network error while saving packages.', false);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var tierPanel = document.getElementById('pricing-tier-form');
    if (tierPanel) bindTierForm(tierPanel);
    var physioPanel = document.getElementById('physio-layout');
    if (physioPanel) bindPhysioLayout(physioPanel);
    var mapper = document.getElementById('chapter-video-mapper');
    if (mapper) bindMapper(mapper);
  });
})();
