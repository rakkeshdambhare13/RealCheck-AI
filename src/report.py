from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from io import BytesIO


def create_pdf_report(
    report_title="RealCheck AI Forensic Analysis Report",
    evidence_records=None,
    final_result=None,
    final_confidence=None,
    uncertainty=None,
    reliability=None,
    evidence_strength=None,
    model_agreement=None,
    image_fake_score=None,
    video_fake_score=None,
    video_result=None
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    story = []

    # ==========================================
    # TITLE
    # ==========================================

    story.append(
        Paragraph(
            report_title,
            title_style
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Multimodal AI-Based Fake Media Detection "
            "and Prediction System",
            styles["Heading3"]
        )
    )

    story.append(
        Spacer(1, 20)
    )

    # ==========================================
    # FINAL ANALYSIS
    # ==========================================

    story.append(
        Paragraph(
            "Final Analysis Result",
            heading_style
        )
    )

    result_data = [
        ["Parameter", "Value"],
        ["Final Result", str(final_result)],
        [
            "Final Confidence",
            (
                f"{final_confidence:.2f}%"
                if final_confidence is not None
                else "N/A"
            )
        ],
        [
            "Uncertainty",
            (
                f"{uncertainty:.2f}%"
                if uncertainty is not None
                else "N/A"
            )
        ],
        [
            "Reliability",
            (
                str(reliability)
                if reliability is not None
                else "N/A"
            )
        ],
        [
            "Evidence Strength",
            (
                str(evidence_strength)
                if evidence_strength is not None
                else "N/A"
            )
        ],
        [
            "Model Agreement",
            (
                str(model_agreement)
                if model_agreement is not None
                else "N/A"
            )
        ]
    ]

    result_table = Table(
        result_data,
        colWidths=[
            2.4 * inch,
            3.5 * inch
        ]
    )

    result_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    story.append(result_table)

    story.append(
        Spacer(1, 20)
    )

    # ==========================================
    # DIGITAL EVIDENCE
    # ==========================================

    story.append(
        Paragraph(
            "Digital Evidence",
            heading_style
        )
    )

    if evidence_records:

        for index, evidence in enumerate(
            evidence_records,
            start=1
        ):

            story.append(
                Paragraph(
                    f"Evidence Record {index}",
                    styles["Heading3"]
                )
            )

            confidence_value = evidence.get(
                "confidence",
                0
            )

            evidence_data = [
                ["Parameter", "Value"],
                [
                    "Evidence ID",
                    str(
                        evidence.get(
                            "evidence_id",
                            "N/A"
                        )
                    )
                ],
                [
                    "File Name",
                    str(
                        evidence.get(
                            "file_name",
                            "N/A"
                        )
                    )
                ],
                [
                    "File Type",
                    str(
                        evidence.get(
                            "file_type",
                            "N/A"
                        )
                    )
                ],
                [
                    "File Size",
                    str(
                        evidence.get(
                            "file_size",
                            "N/A"
                        )
                    )
                ],
                [
                    "Analysis Time",
                    str(
                        evidence.get(
                            "analysis_time",
                            "N/A"
                        )
                    )
                ],
                [
                    "Result",
                    str(
                        evidence.get(
                            "result",
                            "N/A"
                        )
                    )
                ],
                [
                    "Confidence",
                    f"{confidence_value:.2f}%"
                ],
                [
                    "SHA-256",
                    str(
                        evidence.get(
                            "sha256",
                            "N/A"
                        )
                    )
                ]
            ]

            evidence_table = Table(
                evidence_data,
                colWidths=[
                    2.0 * inch,
                    3.9 * inch
                ]
            )

            evidence_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )
                ])
            )

            story.append(evidence_table)

            story.append(
                Spacer(1, 15)
            )

    # ==========================================
    # MULTIMODAL ANALYSIS
    # ==========================================

    if (
        image_fake_score is not None
        or video_fake_score is not None
    ):

        story.append(
            Paragraph(
                "Multimodal Analysis",
                heading_style
            )
        )

        fusion_data = [
            [
                "Modality",
                "Fake Score",
                "Contribution"
            ]
        ]

        if image_fake_score is not None:

            fusion_data.append([
                "Image",
                f"{image_fake_score:.2f}%",
                "40%"
            ])

        if video_fake_score is not None:

            fusion_data.append([
                "Video",
                f"{video_fake_score:.2f}%",
                "60%"
            ])

        fusion_table = Table(
            fusion_data,
            colWidths=[
                2.0 * inch,
                2.0 * inch,
                1.9 * inch
            ]
        )

        fusion_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )

        story.append(fusion_table)

        story.append(
            Spacer(1, 20)
        )

    # ==========================================
    # VIDEO ANALYSIS
    # ==========================================

    if video_result is not None:

        story.append(
            Paragraph(
                "Video Evidence Analysis",
                heading_style
            )
        )

        video_data = [
            ["Parameter", "Value"],
            [
                "Frames Analyzed",
                str(
                    video_result.get(
                        "analyzed_frames",
                        "N/A"
                    )
                )
            ],
            [
                "Fake Frames",
                str(
                    video_result.get(
                        "fake_frames",
                        "N/A"
                    )
                )
            ],
            [
                "Real Frames",
                str(
                    video_result.get(
                        "real_frames",
                        "N/A"
                    )
                )
            ],
            [
                "Fake Frame Ratio",
                f'{video_result.get("fake_ratio", 0):.2f}%'
            ]
        ]

        video_table = Table(
            video_data,
            colWidths=[
                2.5 * inch,
                3.4 * inch
            ]
        )

        video_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )

        story.append(video_table)

        story.append(
            Spacer(1, 15)
        )

        # ==========================================
        # SUSPICIOUS FRAMES
        # ==========================================

        story.append(
            Paragraph(
                "Suspicious Frames",
                styles["Heading3"]
            )
        )

        suspicious = video_result.get(
            "suspicious_frames",
            []
        )

        if suspicious:

            suspicious_data = [
                [
                    "Frame",
                    "Time (s)",
                    "Fake Probability"
                ]
            ]

            for item in suspicious[:20]:

                suspicious_data.append([
                    str(
                        item.get(
                            "frame",
                            "N/A"
                        )
                    ),
                    f'{item.get("time", 0):.2f}',
                    f'{item.get("fake_probability", 0):.2f}%'
                ])

            suspicious_table = Table(
                suspicious_data,
                colWidths=[
                    1.7 * inch,
                    1.7 * inch,
                    2.5 * inch
                ]
            )

            suspicious_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )
                ])
            )

            story.append(
                suspicious_table
            )

        else:

            story.append(
                Paragraph(
                    "No highly suspicious frames detected.",
                    normal_style
                )
            )

    # ==========================================
    # DISCLAIMER
    # ==========================================

    story.append(
        Spacer(1, 25)
    )

    story.append(
        Paragraph(
            "Disclaimer",
            heading_style
        )
    )

    story.append(
        Paragraph(
            "RealCheck AI provides an AI-assisted assessment "
            "of whether digital media is likely real or "
            "AI-generated/manipulated. The result is not "
            "absolute proof of authenticity or manipulation "
            "and should be interpreted together with other "
            "digital forensic evidence.",
            normal_style
        )
    )

    # ==========================================
    # BUILD PDF
    # ==========================================

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()