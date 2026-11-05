from retail_sales.generator import generate_transactions


def test_generator_is_deterministic_and_has_requested_shape(tmp_path):
    first = generate_transactions(tmp_path / "first.csv", rows=100, seed=7, duplicate_count=10)
    second = generate_transactions(tmp_path / "second.csv", rows=100, seed=7, duplicate_count=10)

    assert first.equals(second)
    assert len(first) == 100
    assert first["transaction_id"].duplicated().sum() == 10
    assert (tmp_path / "first.csv").read_bytes() == (tmp_path / "second.csv").read_bytes()
