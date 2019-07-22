import sys
import os
import datetime
import textwrap
import click


try:
    CONSOLE_WIDTH = os.get_terminal_size().columns
except OSError:
    CONSOLE_WIDTH = 80


def display_cmd(cmd, indent=0, wrap=True, script=False):
    indent = ' ' * indent
    leader = '+ '
    initial_indent = indent + leader
    subsequent_indent = indent + (' ' * len(leader))
    if script:
        leader = ''
        initial_indent = ''
        subsequent_indent = '  '
        global CONSOLE_WIDTH
        CONSOLE_WIDTH = 80
        wrap = False if '<<' in cmd else True
    if wrap:
        w = textwrap.TextWrapper(
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
            break_on_hyphens=False,
            break_long_words=False,
            width=(CONSOLE_WIDTH - len(subsequent_indent))
        )
        lines = w.wrap('{}'.format(cmd))
        # Add a space & backslash to the end of each line then remove it from
        # the end of the joined string.
        fancy = '\n'.join(['{} \\'.format(i) for i in lines])[:-2]
    else:
        cmd = cmd.split('\n')
        first = [initial_indent + cmd[0]]
        rest = [i for i in cmd[1:]]
        fancy = '\n'.join(first + rest)

    if not script:
        click.secho(fancy, fg='yellow')
    else:
        sys.stdout.write(fancy + '\n')
    sys.stdout.flush()

def title(msg, script=False, show_date=True):
    timestamp = ''
    if show_date:
        timestamp = ' [{}]'.format(datetime.datetime.now().isoformat())
    if script:
        global CONSOLE_WIDTH
        CONSOLE_WIDTH = 80
        msg = '# {} '.format(msg).ljust(CONSOLE_WIDTH, '-')
    else:
        msg = '{}{} '.format(msg, timestamp).ljust(CONSOLE_WIDTH, '-')
    print()
    if not script:
        click.secho(msg, bold=True)
    else:
        sys.stdout.write(msg + '\n')
    sys.stdout.flush()


def warn(msg, script=False):
    if script:
        sys.stdout.write('# !!! WARNING: {} !!!\n'.format(msg))
    else:
        click.echo(click.style('WARNING: ', fg='yellow', bold=True) +
                   click.style(str(msg), fg='yellow'))
    sys.stdout.flush()


def notify(msg):
    click.echo(click.style('NOTICE: ', fg='blue', bold=True) +
               click.style(str(msg), fg='blue'))
    sys.stdout.flush()


def error(msg, dry_run=False):
    click.echo(click.style('ERROR: ', fg='red', bold=True) +
               click.style(str(msg), fg='red'))
    sys.stdout.flush()
    if not dry_run:
        sys.exit(1)


def password_gen(level='alpha-num', length=10):
    levels = {
        'alpha-lower': string.ascii_lowercase,
        'alpha-mixed': string.ascii_letters,
        'alpha-num': string.ascii_letters + string.digits,
        'alpha-num-symbol': string.ascii_letters + string.digits + string.punctuation
    }
    try:
        source = levels[level]
    except KeyError:
        error('password level not one of: {}'.format(', '.join(levels.keys())))
    return ''.join(random.choices(source, k=length))
