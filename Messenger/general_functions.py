def validate_offset_and_limit(request):
    offset = request.query_params.get('offset') or None
    limit = request.query_params.get('limit') or None

    if offset is not None:
        offset = int(offset)

    if limit is not None:
        limit = int(limit)

    if offset is not None and limit is not None:
        limit = offset + limit

    return offset, limit
