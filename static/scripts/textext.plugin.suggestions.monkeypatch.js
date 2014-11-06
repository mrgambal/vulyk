(function($)
{
	$.fn.textext.TextExtSuggestions.prototype.onGetSuggestions = function(e, data)
	{
		var self        = this,
			suggestions = self.opts("suggestions"),
			scores = [],
			filtered = [];

		/*
		WARNING, WARNING, this method differs from original version.
		Quicksilver search has been integrated here.
		*/

		query = data.query.replace(/\s/g, '');
		if (query.length > 0) {
			$.each(suggestions, function(i) {
				var score = this.score(query);
				
				if (score > 0) {
					scores.push([score, i]);
				}
			});
	
			$.each(scores.sort(function(a, b) {
				return b[0] - a[0];
				}), function(){
					filtered.push(suggestions[this[1]]);
				}
			)

			suggestions = filtered;
		}

		suggestions.push(data.query);
		self.setSuggestions(suggestions);
	};
})(jQuery);
