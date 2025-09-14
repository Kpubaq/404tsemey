import zipfile
import os

def make_submission(output_zip='submission_debug.zip'):
    with zipfile.ZipFile(output_zip, 'w') as z:
        if os.path.exists('examples/results.csv'):
            z.write('examples/results.csv')
        if os.path.exists('debug'):
            for f in os.listdir('debug'):
                z.write(os.path.join('debug', f))

if __name__=='__main__':
    make_submission()
