import os
import shutil
import tempfile
from typing import Any

import matplotlib
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from masscube import read_raw_file_to_obj

matplotlib.use('Agg')

app = FastAPI(title='MassCube EIC Service', version='1.0.0')

allowed_origins = [origin.strip() for origin in os.getenv('EIC_ALLOWED_ORIGINS', '*').split(',') if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


def _to_float_list(values: Any) -> list[float]:
    if values is None:
        return []

    if hasattr(values, 'tolist'):
        values = values.tolist()

    if not isinstance(values, (list, tuple)):
        values = [values]

    result: list[float] = []
    for value in values:
        try:
            result.append(float(value))
        except (TypeError, ValueError):
            continue
    return result


def _parse_mz_values(target_mz_arr: str) -> list[float]:
    parts = [part.strip() for part in target_mz_arr.replace(';', ',').split(',') if part.strip()]
    if not parts:
        raise HTTPException(status_code=422, detail='target_mz_arr is required.')

    values: list[float] = []
    for part in parts:
        try:
            values.append(float(part))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f'Invalid m/z value: {part}') from exc

    return values


def _parse_optional_float(raw: str | None, field: str) -> float | None:
    if raw is None:
        return None

    text = str(raw).strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f'Invalid numeric value for {field}.') from exc


def _normalize_eic_data(eic_data: Any, target_mz_values: list[float]) -> list[dict[str, Any]]:
    if eic_data is None:
        return []

    entries = eic_data if isinstance(eic_data, (list, tuple)) else [eic_data]

    if entries and isinstance(entries[0], (int, float)):
        entries = [entries]

    traces: list[dict[str, Any]] = []

    for index, entry in enumerate(entries):
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue

        time_values = _to_float_list(entry[0])
        signal_values = _to_float_list(entry[1])
        scan_indices = _to_float_list(entry[2]) if len(entry) > 2 else []

        if not time_values or not signal_values:
            continue

        aligned_len = min(len(time_values), len(signal_values))
        mz_value = target_mz_values[index] if index < len(target_mz_values) else None

        traces.append(
            {
                'label': f'm/z {mz_value:.4f}' if mz_value is not None else f'Trace {index + 1}',
                'mz': mz_value,
                'time': time_values[:aligned_len],
                'intensity': signal_values[:aligned_len],
                'scan_index': scan_indices[:aligned_len] if scan_indices else [],
            }
        )

    return traces


@app.get('/api/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/api/eic')
async def extract_eics(
    file: UploadFile = File(...),
    target_mz_arr: str = Form(...),
    target_rt: str | None = Form(None),
    mz_tol: float = Form(0.005),
    rt_tol: float = Form(0.3),
    rt_range_start: str | None = Form(None),
    rt_range_end: str | None = Form(None),
    ylim_min: str | None = Form(None),
    ylim_max: str | None = Form(None),
    show_target_rt: bool = Form(True),
) -> dict[str, Any]:
    if mz_tol <= 0:
        raise HTTPException(status_code=422, detail='mz_tol must be positive.')

    if rt_tol <= 0:
        raise HTTPException(status_code=422, detail='rt_tol must be positive.')

    target_mz_values = _parse_mz_values(target_mz_arr)
    target_rt_value = _parse_optional_float(target_rt, 'target_rt')

    rt_start = _parse_optional_float(rt_range_start, 'rt_range_start')
    rt_end = _parse_optional_float(rt_range_end, 'rt_range_end')

    if (rt_start is None) != (rt_end is None):
        raise HTTPException(status_code=422, detail='Provide both rt_range_start and rt_range_end.')

    rt_range = None
    if rt_start is not None and rt_end is not None:
        if rt_start >= rt_end:
            raise HTTPException(status_code=422, detail='rt_range_start must be smaller than rt_range_end.')
        rt_range = (rt_start, rt_end)

    y_min = _parse_optional_float(ylim_min, 'ylim_min')
    y_max = _parse_optional_float(ylim_max, 'ylim_max')

    if (y_min is None) != (y_max is None):
        raise HTTPException(status_code=422, detail='Provide both ylim_min and ylim_max.')

    ylim = None
    if y_min is not None and y_max is not None:
        if y_min >= y_max:
            raise HTTPException(status_code=422, detail='ylim_min must be smaller than ylim_max.')
        ylim = [y_min, y_max]

    suffix = os.path.splitext(file.filename or '')[1] or '.mzML'
    temp_path = ''

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        raw_obj = read_raw_file_to_obj(temp_path)

        mz_arg: float | list[float] = target_mz_values[0] if len(target_mz_values) == 1 else target_mz_values
        eic_data = raw_obj.plot_eics(
            target_mz_arr=mz_arg,
            target_rt=target_rt_value,
            mz_tol=mz_tol,
            rt_tol=rt_tol,
            rt_range=rt_range,
            output_file_name=None,
            show_target_rt=show_target_rt,
            ylim=ylim,
            return_eic_data=True,
        )

        traces = _normalize_eic_data(eic_data, target_mz_values)
        if not traces:
            raise HTTPException(status_code=422, detail='No EIC traces were extracted from this file and parameter set.')

        return {
            'traces': traces,
            'target_mz_values': target_mz_values,
            'target_rt': target_rt_value,
            'mz_tol': mz_tol,
            'rt_tol': rt_tol,
            'rt_range': list(rt_range) if rt_range else None,
            'ylim': ylim,
            'show_target_rt': show_target_rt,
            'total_points': sum(len(trace['time']) for trace in traces),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Failed to process mzML file: {exc}') from exc
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
