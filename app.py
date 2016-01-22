#! /usr/bin/env python
import shutil
import io
from subprocess          import Popen, PIPE
from werkzeug.wsgi       import wrap_file
from werkzeug.exceptions import MethodNotAllowed, BadRequest
from werkzeug.wrappers   import Request, Response

@Request.application
def application(request):
    if is_valid_request(request):
        page_size           = request.form.get('size') or 'A4'
        page_orientation    = request.form.get('orientation') or 'Portrait'
        
        if is_valid_file_request(request):
            html_file   = request.files['html']
            pdf_file    = generate_pdf(html_file, page_size, page_orientation)
            response    = build_response(request, pdf_file)

        elif is_valid_form_request(request):
            html_param  = request.form.get('html').encode()
            html_file   = io.BytesIO(html_param)
            pdf_file    = generate_pdf(html_file, page_size, page_orientation)
            response    = build_post_response(request, pdf_file)

        else:
            response = BadRequest('html param is required')

    else:
        response = BadRequest('Expect a POST request')

    return response


def is_valid_request(request):
    return request.method == 'POST'


def is_valid_form_request(request):
    html_param     = request.form.get('html')

    return  html_param


def is_valid_file_request(request):
    html_param = request.files.get('html')

    return html_param


def generate_pdf(html_file, size, orientation):
    process = Popen(wkhtmltopdf_cmd(size, orientation), stdin=PIPE, stdout=PIPE)

    shutil.copyfileobj(html_file, process.stdin)
    process.stdin.close()

    return process.stdout


def build_response(request, pdf_file):
    response = Response(wrap_file(request.environ, pdf_file))

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('content-type', 'application/pdf')

    return response


def build_post_response(request, pdf_file, file_name='response.pdf'):
    response = build_response(request, pdf_file)

    response.headers.add('Content-Disposition', header_filename(file_name))
    response.headers.add('Content-Transfer-Encoding', 'binary')

    return response


def header_filename(file_name):
    return "attachment; filename={0}".format(file_name)


def wkhtmltopdf_cmd(size, orientation):
    return ['/usr/bin/wkhtmltopdf.sh', '-q', '-d', '300', '-s', size, '-O', orientation, '-', '-']


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple(
        '127.0.0.1', 5000, application, use_debugger=True, use_reloader=True
    )
