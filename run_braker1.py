#!/usr/bin/python

'''
Run BRAKER1
Author Byoungnam Min on Mar 24, 2015
'''

# Import modules
import sys
import os
from glob import glob
from argparse import ArgumentParser

# Get logging
this_path = os.path.realpath(__file__)
this_dir = os.path.dirname(this_path)
sys.path.append(this_dir)
from set_logging import set_logging

# Parameters
run_hisat2_path = os.path.join(this_dir, 'run_hisat2.py')


# Main function
def main(argv):
    argparse_usage = (
        'run_braker1.py -m <masked_assembly> -b <bam_files> -o <output_dir> '
        '-l <log_dir> -c <num_cores> -C <config_file>'
    )
    parser = ArgumentParser(usage=argparse_usage)
    parser.add_argument(
        "-m", "--maksed_assembly", dest="masked_assembly", nargs=1,
        help="Assembly file in FASTA"
    )
    parser.add_argument(
        "-b", "--bam_fileles", dest="bam_files", nargs='+',
        help="BAM files generated by Hisat2"
    )
    parser.add_argument(
        "-o", "--output_dir", dest="output_dir", nargs='+',
        help="Output directory"
    )
    parser.add_argument(
        "-l", "--log_dir", dest="log_dir", nargs='+',
        help="Log directory"
    )
    parser.add_argument(
        "-c", "--num_cores", dest="num_cores", nargs=1,
        help="Number of cores to be used"
    )
    parser.add_argument(
        "-C", "--config_file", dest="config_file", nargs=1,
        help="Config file generated by check_dependencies.py"
    )
    parser.add_argument(
        '--fungus', dest='fungus_flag', action='store_true',
        help='Fungus flag of BRAKER1'
    )

    args = parser.parse_args()
    if args.masked_assembly:
        masked_assembly = os.path.abspath(args.masked_assembly[0])
    else:
        print '[ERROR] Please provide INPUT ASSEMBLY'
        sys.exit(2)

    if args.bam_files:
        bam_files = [os.path.abspath(x) for x in args.bam_files]
    else:
        print '[ERROR] Please provide BAM FILES'
        sys.exit(2)

    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir[0])
    else:
        print '[ERROR] Please provide OUTPUT DIRECTORY'
        sys.exit(2)

    if args.log_dir:
        log_dir = os.path.abspath(args.log_dir[0])
    else:
        print '[ERROR] Please provide LOG DIRECTORY'
        sys.exit(2)

    if args.num_cores:
        num_cores = args.num_cores[0]
    else:
        num_cores = 1

    if args.log_dir:
        log_dir = os.path.abspath(args.log_dir[0])
    else:
        print '[ERROR] Please provide LOG DIRECTORY'
        sys.exit(2)

    if args.config_file:
        config_file = os.path.abspath(args.config_file[0])
    else:
        print '[ERROR] Please provide CONFIG FILE'
        sys.exit(2)

    if args.fungus_flag:
        fungus_flag = ''
    else:
        fungus_flag = '--fungus'

    # Create necessary dirs
    create_dir(output_dir, log_dir)

    # Set logging
    log_file = os.path.join(
        log_dir, 'pipeline', 'run_braker1.log')
    global logger_time, logger_txt
    logger_time, logger_txt = set_logging(log_file)

    # Run functions :) Slow is as good as Fast
    braker1_bin = parse_config(config_file)
    run_braker1(
        masked_assembly, bam_files, output_dir, log_dir, num_cores,
        braker1_bin, fungus_flag
    )


# Define functions
def import_file(input_file):
    with open(input_file) as f_in:
        txt = (line.rstrip() for line in f_in)
        txt = list(line for line in txt if line)
    return txt


def create_dir(output_dir, log_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    output_base = os.path.basename(output_dir)
    log_output_dir = os.path.join(log_dir, output_base)
    if not os.path.exists(log_output_dir):
        os.mkdir(log_output_dir)

    log_pipeline_dir = os.path.join(log_dir, 'pipeline')
    if not os.path.exists(log_pipeline_dir):
        os.mkdir(log_pipeline_dir)


def parse_config(config_file):
    config_txt = import_file(config_file)
    for line in config_txt:
        if line.startswith('BRAKER1_PATH='):
            braker1_bin = line.replace('BRAKER1_PATH=', '')
            break
    return braker1_bin


def run_braker1(
    masked_assembly, bam_files, output_dir, log_dir, num_cores, braker1_bin,
    fungus_flag
):
    output_base = os.path.basename(output_dir)
    # braker.pl --fungus --softmasking --cores=5
    # --genome=final.assembly.fasta --bam=merged.bam
    # --species=<species> --gff3
    for bam_file in bam_files:
        prefix = (
            os.path.basename(bam_file)
            .replace('.bam', '')
            .replace('_sorted', '')
        )
        gff3_braker1 = os.path.join(
            output_dir, prefix, 'braker1_%s.gff3' % (prefix)
        )
        log_braker = os.path.join(
            log_dir, output_base, 'braker1_%s.log' % (prefix)
        )
        logger_time.debug('START: BRAKER1')

        if not os.path.exists(gff3_braker1):
            os.environ['LD_LIBRARY_PATH'] = os.path.join(
                this_dir, 'external/bamtools-2.3.0/lib'
            )
            os.environ['PATH'] += ':' + os.path.join(
                this_dir, 'external/augustus-3.2.1/bin'
            )
            augustus_config_path = os.path.join(
                this_dir, 'external/augustus-3.2.1/config'
            )
            config_species = os.path.join(
                augustus_config_path, 'species', prefix
            )
            species = prefix
            i = 1
            while os.path.exists(config_species):
                species = prefix + '_' + str(i)
                config_species = os.path.join(
                    augustus_config_path, 'species', species
                )
                i += 1
            os.environ['AUGUSTUS_CONFIG_PATH'] = augustus_config_path
            bamtools_path = os.path.join(
                this_dir, 'external/bamtools-2.3.0/bin'
            )
            genemark_path = os.path.join(
                this_dir, 'external/gm_et_linux_64/gmes_petap'
            )
            samtools_path = os.path.join(
                this_dir, 'external/samtools-1.3/bin'
            )
            working_dir = os.path.join(output_dir, prefix)
            if not os.path.exists(working_dir):
                os.mkdir(working_dir)
            command1 = (
                '%s %s --softmasking --cores=%s --genome=%s '
                '--bam=%s --species=%s --gff3 --AUGUSTUS_CONFIG_PATH=%s '
                '--BAMTOOLS_PATH=%s --GENEMARK_PATH=%s --SAMTOOLS_PATH=%s '
                '--workingdir=%s > %s 2>&1'
            ) % (
                braker1_bin, num_cores, masked_assembly, bam_file,
                species, augustus_config_path, bamtools_path, genemark_path,
                samtools_path, working_dir, log_braker, fungus_flag
            )
            logger_txt.debug('[Run] %s' % (command1))
            os.system(command1)

            # Change file name
            command2 = 'mv %s %s' % (
                glob(os.path.join(
                    output_dir, prefix, 'braker/*', 'augustus.gff3')
                )[0],
                os.path.join(
                    output_dir, prefix,
                    'braker1_%s.gff3' % (prefix)
                )
            )
            logger_txt.debug('[Run] %s' % (command2))
            os.system(command2)

            command3 = 'mv %s %s' % (
                glob(os.path.join(
                    output_dir, prefix, 'braker/*', 'augustus.aa')
                )[0],
                os.path.join(
                    output_dir, prefix,
                    'braker1_%s.faa' % (prefix)
                )
            )
            logger_txt.debug('[Run] %s' % (command3))
            os.system(command3)
        else:
            logger_txt.debug('Braker1 has already been finished')
    logger_time.debug('DONE : Braker1')


if __name__ == "__main__":
    main(sys.argv[1:])
