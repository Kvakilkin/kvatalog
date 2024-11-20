<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script>
    $(document).ready(function() {
        $('#run-parser').click(function() {
            runParser();
        });

        // Обработка нажатия клавиши Enter в любом из полей ввода
        $('#min-price, #max-price, #search-query').keypress(function(event) {
            if (event.which === 13) { // Код клавиши Enter
                runParser();
            }
        });

        function runParser() {
            const minPrice = $('#min-price').val();
            const maxPrice = $('#max-price').val();
            const searchQuery = $('#search-query').val();

            $.post('/ozon_parcer.py', {
                minprice: minPrice,
                maxprice: maxPrice,
                searchquery: searchQuery
            }, function(data) {
                $('#message').text(data.message);
            }).fail(function() {
                $('#message').text('Ошибка при запуске парсера');
            });
        }
    });
</script>