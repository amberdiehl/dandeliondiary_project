from .models import MyBudgetCategory, MyBudget


def helper_get_category_budget(category):

    budget_amount = 0

    children = MyBudgetCategory.objects.filter(parent_category=category)
    if children:
        for child in children:
            child_budgets = MyBudget.objects.filter(category=child).order_by('-effective_date')
            if child_budgets:
                budget_amount += child_budgets[0].amount
    else:
        category_budgets = MyBudget.objects.filter(category=category).order_by('-effective_date')
        if category_budgets:
            budget_amount = category_budgets[0].amount

    return budget_amount
