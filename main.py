from sklearn.metrics import accuracy_score

from fingerprint_data_manager import FingerprintDataManager
from inconsistency_scanner import Scanner
import time
import sys
import pandas as pd

fp_manager = FingerprintDataManager()
scanner = Scanner(number_wrong_fonts=2, number_wrong_features=1, number_transparent_pixels=17200)


PREDICTION_FILE = "results/res_prediction.csv"
REAL_VALUES_FILE = "results/res_real_values.csv"


def generate_analysis_str_vector(fingerprint, scan_results, ground_truth):
    is_consistent = True
    analysis_vector = [fingerprint.countermeasure]
    for analysis_result in scan_results:
        analysis_vector.append(1) if analysis_result.is_consistent else analysis_vector.append(0)
        if not analysis_result.is_consistent:
            is_consistent = False

    analysis_vector.append(1) if is_consistent else analysis_vector.append(0)
    analysis_vector.append(1) if ground_truth else analysis_vector.append(0)
    analysis_vector.append(1) if fingerprint.fpjs2_consistent else analysis_vector.append(0)
    analysis_vector.append(1) if fingerprint.augur_consistent else analysis_vector.append(0)

    return ','.join([str(x) for x in analysis_vector])

def generate_real_values_str_vector(fingerprint, real_os_guessed, real_browser_guessed, ground_truth):
    predict_vec = [
        fingerprint.countermeasure,
        str(ground_truth),
        fingerprint.real_os,
        fingerprint.real_browser,
        real_os_guessed,
        real_browser_guessed
    ]
    return ','.join([str(x) for x in predict_vec])

def scan_fingerprints(fingerprints, prediction_file, real_values_file):
    with open(prediction_file, 'w+') as f_detection, open(real_values_file, 'w+') as f_real_values:
        for counter, fingerprint in enumerate(fingerprints):
            scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
            real_os_guessed, real_browser_guessed, _ = scanner.guess_real_info(fingerprint, scan_results)
            ground_truth = scanner.should_be_consistent(fingerprint)
            analysis_str_vector = generate_analysis_str_vector(fingerprint, scan_results, ground_truth)
            real_values_str_vector = generate_real_values_str_vector(fingerprint, real_os_guessed,
                                                                     real_browser_guessed, ground_truth)

            has_predicted_incons = False in [x.is_consistent for x in scan_results]
            if has_predicted_incons or (real_os_guessed != fingerprint.real_os or  real_browser_guessed != fingerprint.real_browser):
                print("error")
                print(fingerprint)
                print(real_os_guessed, real_browser_guessed)
                for scan_res in scan_results:
                    if not scan_res.is_consistent:
                        print(scan_res)
                print('-----')
            else:
                print('ok:')
                print(fingerprint)

            if counter == 0:
                headers = ",".join(["countermeasure"] + [x.name for x in scan_results] + \
                          ["prediction", "ground_truth", "fpjs2", "augur"])
                f_detection.write('{}\n'.format(headers))

                predict_headers = ["countermeasure", "consistent", "realOs", "realBrowser",
                                   "predictedOs", "predictedBrowser"]

                f_real_values.write('{}\n'.format(",".join(predict_headers)))

            f_detection.write('{}\n'.format(analysis_str_vector))
            f_real_values.write('{}\n'.format(real_values_str_vector))


def analyse_results(prediction_file, real_values_file):
    COUNTERMEASURES = ['no', 'cd', 'ffp', 'ras', 'brave', 'uas', 'cfpb', 'fpr']
    df = pd.read_csv(prediction_file)

    for countermeasure in COUNTERMEASURES:
        sub_df = df[df.countermeasure == countermeasure]
        print('{}, {:d} fingerprints'.format(countermeasure, len(sub_df)))
        df_pred = sub_df['prediction']
        df_truth = sub_df['ground_truth']
        df_fpjs2 = sub_df['fpjs2']
        df_augur = sub_df['augur']
        print("Accuracy FPScanner: {:f} " .format(accuracy_score(df_truth, df_pred)))
        print("Accuracy FPJS2: {:f}".format(accuracy_score(df_truth, df_fpjs2)))
        print("Accuracy Augur: {:f}\n".format(accuracy_score(df_truth, df_augur)))

    df_real_values = pd.read_csv(real_values_file)
    # only for these countermeasures since other don't alter nor the OS or the browser
    for countermeasure in ['ffp', 'ras', 'uas']:
        sub_df = df_real_values[df_real_values.countermeasure == countermeasure]
        nb_fps = len(sub_df)
        nb_rights_browser = len(sub_df[sub_df["realBrowser"] == sub_df["predictedBrowser"]])
        # nb_rights_os = len(sub_df[sub_df["realOs"] == sub_df["predictedOs"]])
        # dont test for pure equality since predicting Linux for ubuntu or fedora is not  wrong, same for windows
        # when the exact version is predicted
        nb_rights_os = 0
        for index, row in sub_df.iterrows():
            if row['realOs'] == row['predictedOs']:
                nb_rights_os += 1
            elif 'Win' in row['realOs'] and 'Win' in row['predictedOs']:
                nb_rights_os += 1
            elif (row['realOs'] in ['Ubuntu', 'Fedora'] and  row['predictedOs'] == 'Linux') or \
                    (row['predictedOs'] in ['Ubuntu', 'Fedora'] and row['realOs'] == 'Linux'):
                nb_rights_os += 1

        accuracy_browser = float(nb_rights_browser / nb_fps)
        accuracy_os = float(nb_rights_os / nb_fps)
        print('{}, {:d} fingerprints'.format(countermeasure, len(sub_df)))
        print("Accuracy OS: %f" % accuracy_os)
        print("Accuracy browser: %f\n" % accuracy_browser)
        # print(sub_df[sub_df["realOs"] != sub_df["predictedOs"]])
        # print(sub_df[sub_df["realBrowser"] != sub_df["predictedBrowser"]])


def run_benchmark(fingerprints):
    # first we run all tests no matter if an  inconsistency is detected
    with open('results/bench_situation1.csv', 'w+') as f_bench1, \
            open('results/bench_situation2.csv', 'w+') as f_bench2, \
            open('results/bench_situation3.csv', 'w+') as f_bench3:
        header_str = 'elapsed_time'
        f_bench1.write('{}\n'.format(header_str))
        f_bench2.write('{}\n'.format(header_str))
        f_bench3.write('{}\n'.format(header_str))

        for counter, fingerprint in enumerate(fingerprints):
            print('Fingerprint', counter)
            # all tests
            start = time.time()
            scanner.check_fingerprint(fingerprint, run_all=True)
            end = time.time()
            f_bench1.write('{:f}\n'.format(end-start))

            # stop when inconsistency found
            start = time.time()
            scanner.check_fingerprint(fingerprint, run_all=False)
            end = time.time()
            f_bench2.write('{:f}\n'.format(end - start))

            # run only pixels test
            start = time.time()
            scanner.check_fingerprint(fingerprint, run_all=False, only_pixels=True)
            end = time.time()
            f_bench3.write('{:f}\n'.format(end - start))


def main(argv):
    if len(argv) > 0 and argv[0] == "cm":
        fingerprints = fp_manager.get_fingerprints_countermeasure(argv[1])
        scan_fingerprints(fingerprints, PREDICTION_FILE, REAL_VALUES_FILE)
    elif len(argv) > 0 and argv[0] == 'analyse':
        analyse_results(PREDICTION_FILE, REAL_VALUES_FILE)
    elif len(argv) > 0 and argv[0] == 'bench':
        fingerprints = fp_manager.get_all_fingerprints()
        run_benchmark(fingerprints)
    else:
        fingerprints = fp_manager.get_all_fingerprints()
        scan_fingerprints(fingerprints, PREDICTION_FILE, REAL_VALUES_FILE)

if __name__ == "__main__":
    main(sys.argv[1:])

