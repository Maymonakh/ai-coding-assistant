Problem:
Create a sorting algorithm in Python (merge sort and quick sort).

Reference Solution:
```python
def merge_sort(numbers):
    # Merge sort: O(n log n), stable
    if len(numbers) <= 1:
        return numbers

    middle = len(numbers) // 2
    left = merge_sort(numbers[:middle])
    right = merge_sort(numbers[middle:])

    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    return result + left[i:] + right[j:]


def quick_sort(numbers):
    # Quick sort: average O(n log n)
    if len(numbers) <= 1:
        return numbers

    pivot = numbers[len(numbers) // 2]
    smaller = [x for x in numbers if x < pivot]
    equal = [x for x in numbers if x == pivot]
    bigger = [x for x in numbers if x > pivot]

    return quick_sort(smaller) + equal + quick_sort(bigger)


print(merge_sort([5, 2, 9, 1]))
print(quick_sort([5, 2, 9, 1]))
```
