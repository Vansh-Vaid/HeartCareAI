"""Report Blueprint - renders and exports prediction reports."""
from __future__ import annotations

import io
import json
from datetime import datetime

from flask import Blueprint, abort, render_template, send_file
from flask_login import login_required
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.feature_contract import get_feature_labels
from .models_db import Doctor, Prediction

report_bp = Blueprint("report", __name__, url_prefix="/report")

FEATURE_LABELS = get_feature_labels()


def _load_prediction_context(prediction: Prediction):
    input_data = json.loads(prediction.input_data or "{}")
    model_summary = json.loads(prediction.model_results or "{}")
    explanation = json.loads(prediction.explanation_json or "{}")
    input_audit = json.loads(prediction.input_audit or "[]")
    assigned_doctor = None
    if prediction.patient and prediction.patient.doctor_id:
        assigned_doctor = Doctor.query.get(prediction.patient.doctor_id)
    return input_data, model_summary, explanation, input_audit, assigned_doctor


def _build_pdf(prediction: Prediction) -> bytes:
    input_data, model_summary, explanation, input_audit, assigned_doctor = _load_prediction_context(prediction)
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.white,
        alignment=TA_CENTER,
        backColor=colors.HexColor("#12344A"),
        spaceAfter=8,
    )
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#12344A"))
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=14)

    story.append(Paragraph("HeartCare AI Screening Report", title_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D7E1E6")))
    story.append(Spacer(1, 10))

    summary_table = Table(
        [
            ["Report ID", f"RPT-{prediction.id:05d}", "Model", prediction.model_name or "Promoted model"],
            ["Probability", f"{prediction.risk_probability * 100:.1f}%", "Threshold", f"{prediction.threshold_used * 100:.1f}%"],
            ["Risk band", prediction.risk_level, "Confidence", prediction.confidence_label or "N/A"],
            ["Generated", prediction.created_at.strftime("%Y-%m-%d %H:%M UTC"), "Version", prediction.model_version or "N/A"],
        ],
        colWidths=[3.2 * cm, 5.0 * cm, 3.2 * cm, 5.0 * cm],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#F7FAF9"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E1E6")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Result interpretation", section_style))
    story.append(Paragraph(explanation.get("summary", "No explanation available."), body_style))
    story.append(Paragraph(explanation.get("disclaimer", ""), body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Values used in this screening", section_style))
    input_rows = [["Feature", "Value", "Reference"]]
    for feature, value in input_data.items():
        label, unit, _minimum, _maximum = FEATURE_LABELS.get(feature, (feature, "", None, None))
        reference = FEATURE_LABELS.get(feature, (feature, unit, None, None))[1]
        input_rows.append([label, str(value), reference])
    input_table = Table(input_rows, colWidths=[5.2 * cm, 4.2 * cm, 6.2 * cm])
    input_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12344A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F7FAF9"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E1E6")),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ]
        )
    )
    story.append(input_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Model details", section_style))
    story.append(
        Paragraph(
            (
                f"The promoted model for this report is <b>{prediction.model_name or 'the selected production model'}</b>. "
                f"It produced a risk estimate of <b>{prediction.risk_probability * 100:.1f}%</b> "
                f"against an alert level of <b>{prediction.threshold_used * 100:.1f}%</b>."
            ),
            body_style,
        )
    )

    if explanation.get("drivers"):
        story.append(Spacer(1, 6))
        story.append(Paragraph("Potential drivers", section_style))
        for item in explanation["drivers"]:
            story.append(Paragraph(f"- {item}", body_style))

    if explanation.get("supporting_factors"):
        story.append(Spacer(1, 6))
        story.append(Paragraph("Supporting context", section_style))
        for item in explanation["supporting_factors"]:
            story.append(Paragraph(f"- {item}", body_style))

    if input_audit:
        story.append(Spacer(1, 6))
        story.append(Paragraph("Input audit", section_style))
        for item in input_audit:
            story.append(Paragraph(f"- {item}", body_style))

    if assigned_doctor:
        story.append(Spacer(1, 6))
        story.append(Paragraph("Assigned doctor", section_style))
        story.append(
            Paragraph(
                f"{assigned_doctor.name} - {assigned_doctor.specialization}, {assigned_doctor.hospital}. "
                f"Contact: {assigned_doctor.phone or 'N/A'} / {assigned_doctor.email or 'N/A'}",
                body_style,
            )
        )

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Medical disclaimer: this report is an AI-assisted screening summary and does not replace a qualified clinician.",
            body_style,
        )
    )

    document.build(story)
    buffer.seek(0)
    return buffer.read()


@report_bp.route("/download/<int:pred_id>")
@login_required
def download(pred_id):
    prediction = Prediction.query.get_or_404(pred_id)
    try:
        pdf_bytes = _build_pdf(prediction)
    except Exception as exc:  # pragma: no cover - surfaced to the UI.
        abort(500, description=f"PDF generation failed: {exc}")
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"HeartCare_Report_{pred_id}.pdf",
    )


@report_bp.route("/view/<int:pred_id>")
@login_required
def view(pred_id):
    prediction = Prediction.query.get_or_404(pred_id)
    input_data, model_summary, explanation, input_audit, assigned_doctor = _load_prediction_context(prediction)
    return render_template(
        "report/view.html",
        pred=prediction,
        inp=input_data,
        model_summary=model_summary,
        explanation=explanation,
        input_audit=input_audit,
        assigned_doc=assigned_doctor,
        feature_labels=FEATURE_LABELS,
    )
