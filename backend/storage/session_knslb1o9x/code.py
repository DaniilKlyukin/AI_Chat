def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                # Подсчет количества обменов
                count_swaps = 1
        # Выводим каждый шаг сортировки
        print("Step ", i+1, arr)
    return arr

# Тестирование
arr = [64, 34, 25, 12, 22, 11, 90]
print("Original array:", arr)
print("Sorted array:", bubble_sort(arr))