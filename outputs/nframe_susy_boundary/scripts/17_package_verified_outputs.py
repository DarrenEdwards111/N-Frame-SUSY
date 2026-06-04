from verified_metadata_common import ensure_dirs, package_outputs


def main():
    ensure_dirs()
    output = package_outputs()
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
