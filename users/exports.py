"""Build Excel and PDF reports of website traffic for marketing."""
from __future__ import annotations

import io
import zipfile
from datetime import date
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.utils import timezone

from users.insights import insight_bundle


def _stamp():
    return timezone.localtime().strftime('%Y-%m-%d')


def _cell(col, row, value):
    ref = f'{chr(65 + col)}{row}'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"><v>{int(value)}</v></c>'
    text = escape('' if value is None else str(value))
    return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def _row_xml(row_num, values):
    cells = ''.join(_cell(i, row_num, v) for i, v in enumerate(values))
    return f'<row r="{row_num}">{cells}</row>'


def _section_rows(report):
    day = report['day']
    title = f'Tio Academy insights {day.isoformat()}' if day else 'Tio Academy website insights'
    rows = [[title], [f'Exported {_stamp()}'], []]
    h = report['headline']
    rows.append(['Visitors', h['unique_visitors']])
    rows.append(['Traffic (page opens)', h['page_views']])
    rows.append(['Clicked buy', h['buy_clicks']])
    rows.append(['Bought', h['purchases']])
    if not day:
        rows.append(['Bought in total (all recorded payments)', report['traffic']['purchases_ever']])
    rows.append([])
    rows.append(['Countries', 'Opens'])
    for row in report['countries'] or [{'label': 'No country data yet', 'count': 0}]:
        rows.append([row['label'], row['count']])
    rows.append([])
    rows.append(['Devices', 'Opens'])
    for row in report['devices'] or [{'label': 'No device data yet', 'count': 0}]:
        rows.append([row['label'], row['count']])
    rows.append([])
    rows.append(['Most opened pages', 'Opens'])
    for row in report['pages'] or [{'label': 'No page data yet', 'count': 0}]:
        rows.append([row['label'], row['count']])
    rows.append([])
    rows.append(['Buy clicks (what they tried to pay)', 'Clicks'])
    for row in report['buy_clicks'] or [{'label': 'No buy clicks yet', 'count': 0}]:
        rows.append([row['label'], row['count']])
    rows.append([])
    rows.append(['Paid items', 'When', 'Amount'])
    if report['paid_items']:
        for row in report['paid_items']:
            when = row['when'].strftime('%Y-%m-%d %H:%M') if row.get('when') else ''
            rows.append([row['label'], when, row.get('amount') or 0])
    else:
        rows.append(['No purchases this period', '', 0])
    rows.append([])
    rows.append(['Day', 'People', 'Page opens', 'Clicked buy', 'Bought'])
    for day_row in report['daily']:
        rows.append([
            day_row['day'].isoformat() if isinstance(day_row['day'], date) else str(day_row['day']),
            day_row['unique_visitors'],
            day_row['page_views'],
            day_row['buy_clicks'],
            day_row['purchases'],
        ])
    if not report['daily']:
        rows.append(['No daily rows yet', 0, 0, 0, 0])
    return rows


def build_xlsx_bytes(day=None):
    rows = _section_rows(insight_bundle(day))
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>'
        + ''.join(_row_xml(i, r) for i, r in enumerate(rows, start=1))
        + '</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Insights" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('xl/workbook.xml', workbook)
        zf.writestr('xl/_rels/workbook.xml.rels', wb_rels)
        zf.writestr('xl/worksheets/sheet1.xml', sheet)
    return buf.getvalue()


def _pdf_escape(text):
    return str(text).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _wrap(text, width=92):
    text = str(text)
    if len(text) <= width:
        return [text]
    parts = []
    while text:
        parts.append(text[:width])
        text = text[width:]
    return parts


def _pdf_lines(day=None):
    report = insight_bundle(day)
    h = report['headline']
    title = f'Tio Academy insights {day.isoformat()}' if day else 'Tio Academy website insights'
    lines = [(title, 16), (f'Exported {_stamp()}', 11), ('', 11)]
    lines.append((f"People: {h['unique_visitors']}   Traffic: {h['page_views']} opens", 12))
    lines.append((f"Clicked buy: {h['buy_clicks']}   Bought: {h['purchases']}", 12))
    if not day:
        lines.append((f"Bought in total: {report['traffic']['purchases_ever']}", 11))
    lines.append(('', 11))
    lines.append(('Countries', 13))
    for row in report['countries'] or [{'label': 'No country data yet', 'count': 0}]:
        lines.append((f"{row['label']}: {row['count']}", 11))
    lines.append(('', 11))
    lines.append(('Devices', 13))
    for row in report['devices'] or [{'label': 'No device data yet', 'count': 0}]:
        lines.append((f"{row['label']}: {row['count']}", 11))
    lines.append(('', 11))
    lines.append(('Most opened pages', 13))
    for row in report['pages'] or [{'label': 'No page data yet', 'count': 0}]:
        for part in _wrap(f"{row['label']} - {row['count']}"):
            lines.append((part, 11))
    lines.append(('', 11))
    lines.append(('What they clicked to pay', 13))
    for row in report['buy_clicks'] or [{'label': 'No buy clicks yet', 'count': 0}]:
        for part in _wrap(f"{row['label']} - {row['count']}"):
            lines.append((part, 11))
    lines.append(('', 11))
    lines.append(('What they paid', 13))
    if report['paid_items']:
        for row in report['paid_items']:
            when = row['when'].strftime('%Y-%m-%d') if row.get('when') else ''
            for part in _wrap(f"{when} {row['label']}  {row.get('amount') or 0}"):
                lines.append((part, 11))
    else:
        lines.append(('No purchases this period.', 11))
    lines.append(('', 11))
    lines.append(('Daily traffic', 13))
    lines.append(('Day            People   Opens    Buy      Bought', 11))
    if report['daily']:
        for day_row in report['daily']:
            day_s = day_row['day'].isoformat() if isinstance(day_row['day'], date) else str(day_row['day'])
            lines.append((
                f"{day_s:<14} {day_row['unique_visitors']:<8} {day_row['page_views']:<8} "
                f"{day_row['buy_clicks']:<8} {day_row['purchases']}",
                11,
            ))
    else:
        lines.append(('No daily rows yet.', 11))
    return lines


def _pdf_page_streams(day=None):
    pages = []
    commands = []
    y = 792
    for text, size in _pdf_lines(day):
        if y < 48:
            pages.append('\n'.join(commands).encode('latin-1', 'replace'))
            commands = []
            y = 792
        if text:
            commands.append(f'BT /F1 {size} Tf 40 {y} Td ({_pdf_escape(text)}) Tj ET')
        y -= 20 if size >= 13 else 16
    pages.append('\n'.join(commands).encode('latin-1', 'replace'))
    return pages


def build_pdf_bytes(day=None):
    streams = _pdf_page_streams(day)
    n = len(streams)
    font_id = 3
    page_ids = list(range(4, 4 + n))
    content_ids = list(range(4 + n, 4 + 2 * n))
    bodies = {
        1: b'<< /Type /Catalog /Pages 2 0 R >>',
        2: (
            f'<< /Type /Pages /Count {n} /Kids [{" ".join(f"{i} 0 R" for i in page_ids)}] >>'
        ).encode('ascii'),
        3: b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    }
    for page_id, content_id, stream in zip(page_ids, content_ids, streams):
        bodies[page_id] = (
            f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
            f'/Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>'
        ).encode('ascii')
        bodies[content_id] = (
            f'<< /Length {len(stream)} >>\nstream\n'.encode('ascii') + stream + b'\nendstream'
        )
    buf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for obj_id in range(1, max(bodies) + 1):
        offsets.append(len(buf))
        buf.extend(f'{obj_id} 0 obj\n'.encode('ascii'))
        buf.extend(bodies[obj_id])
        buf.extend(b'\nendobj\n')
    xref_pos = len(buf)
    buf.extend(f'xref\n0 {len(offsets)}\n'.encode('ascii'))
    buf.extend(b'0000000000 65535 f \n')
    for off in offsets[1:]:
        buf.extend(f'{off:010d} 00000 n \n'.encode('ascii'))
    buf.extend(
        f'trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n'
        .encode('ascii')
    )
    return bytes(buf)


def excel_response(day=None):
    data = build_xlsx_bytes(day)
    suffix = day.isoformat() if day else _stamp()
    response = HttpResponse(
        data,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="Tio-Academy-insights-{suffix}.xlsx"'
    return response


def pdf_response(day=None):
    data = build_pdf_bytes(day)
    suffix = day.isoformat() if day else _stamp()
    response = HttpResponse(data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Tio-Academy-insights-{suffix}.pdf"'
    return response
