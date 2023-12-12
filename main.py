from argparse import ArgumentParser

def get_params():
    parser = ArgumentParser()
    parser.add_argument('--data_path', type=str, default='data')
    return parser.parse_args()

def main():
    args = get_params()
    print(args.data_path)

if __name__ == '__main__':
    main()