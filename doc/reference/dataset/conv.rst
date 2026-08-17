:tocdepth: 3

.. automodule:: guidata.dataset.conv

Strict JSON deserialization
---------------------------

The default :func:`guidata.dataset.json_to_dataset` behavior is intentionally permissive for backward compatibility. Unknown persisted fields are ignored, while fields absent from the payload receive their current defaults. This remains suitable for ordinary settings where accepting additions and removals is desirable.

Scientific parameters, long-lived persisted data, and data received across a trust boundary may instead require schema drift to be reported. Pass ``strict=True`` and, when the expected type is known, ``expected_class``. Validation then happens before the class is constructed:

.. code-block:: python

	import guidata.dataset as gds

	class FitParam(gds.DataSet):
		amplitude = gds.FloatItem("Amplitude", default=1.0, min=0.0)

	restored = gds.json_to_dataset(
		json_text,
		strict=True,
		expected_class=FitParam,
	)

Using ``expected_class`` also prevents a payload from causing an unexpected import. Strict validation reports missing, unknown, and invalid fields together through :class:`guidata.dataset.DataSetJSONValidationError`:

.. code-block:: python

	try:
		restored = gds.json_to_dataset(
			json_text,
			strict=True,
			expected_class=FitParam,
		)
	except gds.DataSetJSONValidationError as error:
		print("Missing:", sorted(error.missing_fields))
		print("Unknown:", sorted(error.unknown_fields))
		print("Invalid:", error.invalid_fields)

Every serializable input field is required in strict mode, even when the current class defines a default. This catches renamed fields instead of silently substituting that default. Applications may opt individual additions into defaulting through ``allowed_missing``; nested fields use dotted paths:

.. code-block:: python

	restored = gds.json_to_dataset(
		json_text,
		strict=True,
		expected_class=FitParam,
		allowed_missing={"tolerance", "bounds.minimum"},
	)

An unknown ``allowed_missing`` path is rejected, so a typo cannot accidentally weaken validation. ``allow_none`` controls whether a present value may be ``None``; it does not make a field optional. Structural group markers and button items are not persisted. Computed items found in historical output are recognized but ignored on input, while ordinary display-only ``readonly`` items remain persisted inputs.

Application-owned versions and migrations
-----------------------------------------

Data schema versions belong to the application. :func:`guidata.dataset.dataset_to_json` does not write a mandatory version, so existing JSON remains unchanged. An application may add the reserved ``schema_version`` key to the decoded object before storing it:

.. code-block:: python

	import json

	payload = json.loads(gds.dataset_to_json(FitParam(amplitude=2.5)))
	payload["schema_version"] = 2
	json_text = json.dumps(payload)

``expected_version`` is the maximum version understood by the caller. An absent or older version is accepted, but a future version fails before migration and before the DataSet constructor runs. A migration receives a deep copy of the complete payload and the source version. It may mutate that copy, but must return a JSON object:

.. code-block:: python

	def migrate_fit(payload, source_version):
		if source_version in (None, 1):
			payload["amplitude"] = float(payload.pop("a"))
			payload["schema_version"] = 2
		return payload

	restored = gds.json_to_dataset(
		historical_json,
		strict=True,
		expected_class=FitParam,
		expected_version=2,
		migrate=migrate_fit,
	)

The migrated mapping is revalidated strictly. A migration that leaves ``a`` behind, omits ``amplitude``, changes the class identity, or produces an invalid value therefore fails before construction. Exceptions raised by the migration itself are propagated to the caller.

The ``x-guidata-version`` value produced by :func:`guidata.dataset.dataset_to_schema` is unrelated: it versions guidata's frontend-oriented JSON Schema document, not application data. Dynamic choices that depend on a DataSet instance can only receive representation-level checks before construction; applications should perform domain-specific migration checks when those choices change between versions.
