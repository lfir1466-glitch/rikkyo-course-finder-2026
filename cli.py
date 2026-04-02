#!/usr/bin/env python3
"""CLI interface for Rikkyo University course search.

Usage:
    python3 cli.py search --department 文学部 --course-name 英語
    python3 cli.py search --campus 池袋 --teacher 田中 --page 2
    python3 cli.py detail --code AF182
    python3 cli.py search-detail --department 経済学部 --top 3
    python3 cli.py schema
    python3 cli.py list-options
"""
import argparse
import json
import sys

from scraper import (
    resolve_params, easy_search, easy_search_with_evaluations,
    safe_search, safe_detail, safe_search_with_evaluations,
    search_and_detail, search_and_detail_parallel,
    get_syllabus_detail,
    natural_search, parse_natural_query,
    compare_courses, check_schedule_conflicts, build_timetable,
    GAKUBU_MAP, BUNRUI19_MAP, BUNRUI3_MAP, BUNRUI12_MAP, BUNRUI2_MAP,
)


def _json_out(data):
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def cmd_search(args):
    kwargs = {}
    if args.department:
        kwargs["department"] = args.department
    if args.course_name:
        kwargs["course_name"] = args.course_name
    if args.teacher:
        kwargs["teacher"] = args.teacher
    if args.campus:
        kwargs["campus"] = args.campus
    if args.category:
        kwargs["category"] = args.category
    if args.format:
        kwargs["format"] = args.format
    if args.registration:
        kwargs["registration"] = args.registration
    if args.year:
        kwargs["year"] = args.year
    if args.course_code:
        kwargs["course_code"] = args.course_code
    if args.numbering:
        kwargs["numbering"] = args.numbering
    if args.keyword:
        for i, kw in enumerate(args.keyword[:3], 1):
            kwargs[f"keyword_{i}"] = kw

    if args.exam_filter != "all" or args.exam_max < 100 or args.report_min > 0:
        result = safe_search_with_evaluations(
            page=args.page,
            exam_filter=args.exam_filter,
            exam_max=args.exam_max,
            report_min=args.report_min,
            **resolve_params(**kwargs),
        )
    else:
        result = safe_search(page=args.page, **resolve_params(**kwargs))

    _json_out(result)


def cmd_detail(args):
    result = safe_detail(nendo=args.year, kodo_2=args.code)
    _json_out(result)


def cmd_search_detail(args):
    kwargs = {}
    if args.department:
        kwargs["department"] = args.department
    if args.course_name:
        kwargs["course_name"] = args.course_name
    if args.teacher:
        kwargs["teacher"] = args.teacher
    if args.campus:
        kwargs["campus"] = args.campus
    if args.category:
        kwargs["category"] = args.category
    if args.format:
        kwargs["format"] = args.format
    if args.year:
        kwargs["year"] = args.year
    if args.keyword:
        for i, kw in enumerate(args.keyword[:3], 1):
            kwargs[f"keyword_{i}"] = kw

    result = search_and_detail_parallel(top_n=args.top, **kwargs)
    _json_out(result)


def cmd_schema(_args):
    schema = {
        "commands": {
            "search": {
                "description": "Search courses with filters. Returns paginated results.",
                "params": {
                    "department": {
                        "description": "学部名 (Department name in Japanese or numeric ID)",
                        "type": "string",
                        "values": {k: v for k, v in GAKUBU_MAP.items() if k},
                    },
                    "course_name": {
                        "description": "科目名 (Course name, partial match)",
                        "type": "string",
                    },
                    "teacher": {
                        "description": "教員名 (Teacher name, partial match)",
                        "type": "string",
                    },
                    "campus": {
                        "description": "校地 (Campus)",
                        "type": "string",
                        "values": {k: v for k, v in BUNRUI12_MAP.items() if k},
                    },
                    "category": {
                        "description": "科目設置区分 (Course category)",
                        "type": "string",
                        "values": {k: v for k, v in BUNRUI19_MAP.items() if k},
                    },
                    "format": {
                        "description": "授業形態 (Class format: in-person, online, etc.)",
                        "type": "string",
                        "values": {k: v for k, v in BUNRUI3_MAP.items() if k},
                    },
                    "registration": {
                        "description": "履修登録方法 (Registration method)",
                        "type": "string",
                        "values": {k: v for k, v in BUNRUI2_MAP.items() if k},
                    },
                    "year": {
                        "description": "年度 (Academic year, default: 2025)",
                        "type": "string",
                        "default": "2026",
                    },
                    "course_code": {
                        "description": "科目コード (Course code, e.g. AF182)",
                        "type": "string",
                    },
                    "numbering": {
                        "description": "科目ナンバリング (Course numbering, e.g. EDU3700)",
                        "type": "string",
                    },
                    "keyword": {
                        "description": "シラバス内キーワード (Up to 3 keywords to search within syllabus)",
                        "type": "array",
                        "max_items": 3,
                    },
                    "page": {
                        "description": "Page number (20 results per page)",
                        "type": "integer",
                        "default": 1,
                    },
                    "exam_filter": {
                        "description": "Filter by exam type",
                        "type": "string",
                        "values": ["all", "has-exam", "no-exam", "has-report"],
                        "default": "all",
                    },
                    "exam_max": {
                        "description": "Maximum exam percentage (0-100)",
                        "type": "integer",
                        "default": 100,
                    },
                    "report_min": {
                        "description": "Minimum report percentage (0-100)",
                        "type": "integer",
                        "default": 0,
                    },
                },
            },
            "detail": {
                "description": "Get full syllabus detail for a specific course.",
                "params": {
                    "code": {
                        "description": "科目コード (Course code)",
                        "type": "string",
                        "required": True,
                    },
                    "year": {
                        "description": "年度 (Academic year)",
                        "type": "string",
                        "default": "2026",
                    },
                },
            },
            "search-detail": {
                "description": "Search courses and fetch full syllabus for top N results in one call.",
                "params": {
                    "top": {
                        "description": "Number of top results to fetch details for",
                        "type": "integer",
                        "default": 5,
                    },
                },
                "note": "Accepts all search params plus 'top'. Details fetched in parallel.",
            },
            "schema": {
                "description": "Output this schema as JSON.",
                "params": {},
            },
            "list-options": {
                "description": "List all valid option values for dropdown/enum fields.",
                "params": {},
            },
        },
        "response_format": {
            "ok": "boolean - true if request succeeded",
            "data": "object - result data (when ok=true)",
            "error": "string - error code (when ok=false)",
            "message": "string - error description (when ok=false)",
        },
        "error_codes": {
            "network_error": "Upstream server unreachable or timed out",
            "parse_error": "HTML response could not be parsed",
            "no_results": "Search returned 0 results (noted in data, not an error)",
            "not_found": "Detail page not found or empty",
        },
    }
    _json_out(schema)


def cmd_nl_search(args):
    result = natural_search(args.query, page=args.page)
    _json_out(result)


def cmd_compare(args):
    codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    result = compare_courses(codes, nendo=args.year)
    _json_out(result)


def cmd_conflicts(args):
    courses = json.loads(args.courses)
    result = check_schedule_conflicts(courses)
    _json_out(result)


def cmd_timetable(args):
    courses = json.loads(args.courses)
    result = build_timetable(courses)
    _json_out(result)


def cmd_list_options(_args):
    options = {
        "department (gakubu)": {v: k for k, v in GAKUBU_MAP.items() if k},
        "category (bunrui19)": {v: k for k, v in BUNRUI19_MAP.items() if k},
        "format (bunrui3)": {v: k for k, v in BUNRUI3_MAP.items() if k},
        "campus (bunrui12)": {v: k for k, v in BUNRUI12_MAP.items() if k},
        "registration (bunrui2)": {v: k for k, v in BUNRUI2_MAP.items() if k},
    }
    _json_out(options)


def main():
    parser = argparse.ArgumentParser(
        description="Rikkyo University course search CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # search
    sp_search = subparsers.add_parser("search", help="Search courses")
    sp_search.add_argument("--department", "-d", help="学部名")
    sp_search.add_argument("--course-name", "-n", help="科目名")
    sp_search.add_argument("--teacher", "-t", help="教員名")
    sp_search.add_argument("--campus", "-c", help="校地")
    sp_search.add_argument("--category", help="科目設置区分")
    sp_search.add_argument("--format", "-f", help="授業形態")
    sp_search.add_argument("--registration", help="履修登録方法")
    sp_search.add_argument("--year", "-y", default="2026", help="年度")
    sp_search.add_argument("--course-code", help="科目コード")
    sp_search.add_argument("--numbering", help="科目ナンバリング")
    sp_search.add_argument("--keyword", "-k", action="append", help="キーワード (max 3)")
    sp_search.add_argument("--page", "-p", type=int, default=1, help="Page number")
    sp_search.add_argument("--exam-filter", default="all",
                           choices=["all", "has-exam", "no-exam", "has-report"])
    sp_search.add_argument("--exam-max", type=int, default=100, help="Max exam %% (0-100)")
    sp_search.add_argument("--report-min", type=int, default=0, help="Min report %% (0-100)")
    sp_search.set_defaults(func=cmd_search)

    # detail
    sp_detail = subparsers.add_parser("detail", help="Get syllabus detail")
    sp_detail.add_argument("--code", required=True, help="科目コード")
    sp_detail.add_argument("--year", "-y", default="2026", help="年度")
    sp_detail.set_defaults(func=cmd_detail)

    # search-detail
    sp_sd = subparsers.add_parser("search-detail", help="Search + fetch details")
    sp_sd.add_argument("--department", "-d", help="学部名")
    sp_sd.add_argument("--course-name", "-n", help="科目名")
    sp_sd.add_argument("--teacher", "-t", help="教員名")
    sp_sd.add_argument("--campus", "-c", help="校地")
    sp_sd.add_argument("--category", help="科目設置区分")
    sp_sd.add_argument("--format", "-f", help="授業形態")
    sp_sd.add_argument("--year", "-y", default="2026", help="年度")
    sp_sd.add_argument("--keyword", "-k", action="append", help="キーワード")
    sp_sd.add_argument("--top", type=int, default=5, help="Number of results to get details for")
    sp_sd.set_defaults(func=cmd_search_detail)

    # nl-search
    sp_nl = subparsers.add_parser("nl-search", help="Search using natural language query")
    sp_nl.add_argument("query", help="Natural language query (e.g. '月曜2限の経済学部の英語')")
    sp_nl.add_argument("--page", "-p", type=int, default=1, help="Page number")
    sp_nl.set_defaults(func=cmd_nl_search)

    # compare
    sp_cmp = subparsers.add_parser("compare", help="Compare multiple courses")
    sp_cmp.add_argument("--codes", required=True, help="Comma-separated course codes")
    sp_cmp.add_argument("--year", "-y", default="2026", help="年度")
    sp_cmp.set_defaults(func=cmd_compare)

    # conflicts
    sp_conf = subparsers.add_parser("conflicts", help="Check schedule conflicts")
    sp_conf.add_argument("--courses", required=True,
                         help='JSON array: [{"code":"A1","name":"Math","schedule":"月1"},...]')
    sp_conf.set_defaults(func=cmd_conflicts)

    # timetable
    sp_tt = subparsers.add_parser("timetable", help="Build timetable from courses")
    sp_tt.add_argument("--courses", required=True,
                       help='JSON array: [{"code":"A1","name":"Math","schedule":"月1"},...]')
    sp_tt.set_defaults(func=cmd_timetable)

    # schema
    sp_schema = subparsers.add_parser("schema", help="Output API schema as JSON")
    sp_schema.set_defaults(func=cmd_schema)

    # list-options
    sp_opts = subparsers.add_parser("list-options", help="List valid option values")
    sp_opts.set_defaults(func=cmd_list_options)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
