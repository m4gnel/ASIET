#include <stdio.h>
#include <stdlib.h>  // Necessary for malloc and free

struct Node {
    int data;
    struct Node* next;
};

void insertAtBeginning(struct Node** head, int newData) {
    struct Node* newNode = (struct Node*)malloc(sizeof(struct Node));
    newNode->data = newData;
    newNode->next = *head;
    *head = newNode;
}

void deleteFromBeginning(struct Node** head) {
    if (*head == NULL) {
        printf("List is empty, nothing to delete.\n");
        return;
    }
    struct Node* temp = *head;
    *head = (*head)->next;
    free(temp);
}

void printList(struct Node* node) {
    while (node != NULL) {
        printf("%d -> ", node->data);
        node = node->next;
    }
    printf("NULL\n");
}

int main() {
    struct Node* head = NULL;

    insertAtBeginning(&head, 10);
    insertAtBeginning(&head, 20);
    insertAtBeginning(&head, 30);

    printf("Linked List after insertions at the beginning:\n");
    printList(head);

    deleteFromBeginning(&head);
    printf("Linked List after deletion from the beginning:\n");
    printList(head);

    deleteFromBeginning(&head);
    printf("Linked List after another deletion from the beginning:\n");
    printList(head);

    deleteFromBeginning(&head);
    printf("Linked List after deleting the last element:\n");
    printList(head);

    deleteFromBeginning(&head);

    return 0;
}
